import inspect
import sqlite3

import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.config import Config
from wanderlens.core.models import Destination
from wanderlens.core.recommend import (
    destination_text,
    rank_destinations,
    taste_attribute_weights,
    taste_embedding,
)
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import load_taste_facets, run_recommend


def _embed_text(text):
    vector = np.zeros(3, dtype=np.float32)
    lowered = text.lower()
    if "coast" in lowered:
        vector[0] = 1.0
    if "mountain" in lowered:
        vector[1] = 1.0
    if "city" in lowered:
        vector[2] = 1.0
    if vector.sum() == 0:
        vector[0] = 1.0
    return vector / np.linalg.norm(vector)


class FakeEmbedder:
    dim = 3

    def embed_text(self, text):
        return _embed_text(text)

    def embed_image(self, path):
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)


class CountingEmbedder(FakeEmbedder):
    def __init__(self):
        self.text_calls = 0

    def embed_text(self, text):
        self.text_calls += 1
        return super().embed_text(text)


def test_cases_built_for_final_recommendations_only(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "wanderlens.catalog.case.gather_facts",
        lambda d, session=None: {"extract": "x", "page_url": "", "wikidata_id": ""},
    )
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    class CountingWriter:
        model = "m"
        prompt_version = "v"

        def __init__(self):
            self.calls = 0

        def write(self, destination, facts, search_results):
            self.calls += 1
            return {"narrative": "case", "sources": []}

    writer = CountingWriter()
    recs = run_recommend(
        config, count=2, embedder=FakeEmbedder(), catalog=catalog, case_writer=writer
    )

    assert recs
    assert writer.calls == len(recs)


def test_run_history_and_impressions(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    run_recommend(config, count=2, embedder=FakeEmbedder(), catalog=catalog)
    run_recommend(config, count=2, embedder=FakeEmbedder(), catalog=catalog)

    conn = connect(config.db_path)
    runs = [row[0] for row in conn.execute("SELECT DISTINCT run_id FROM recommendations ORDER BY run_id")]
    assert runs == [1, 2]
    impressions = conn.execute("SELECT COUNT(*) FROM impressions WHERE run_id = 2").fetchone()[0]
    assert impressions == 2


def test_feedback_bias_is_deterministic(tmp_path):
    import numpy as np

    from wanderlens.pipeline.recommend import load_feedback_bias

    config = _seed(tmp_path)
    conn = connect(config.db_path)
    for dest_id, vector in (("a", [1.0, 0.0]), ("b", [0.0, 1.0])):
        conn.execute(
            "INSERT INTO destination_embeddings (destination_id, model, dim, vector) VALUES (?, 'm', 2, ?)",
            (dest_id, np.array(vector, dtype=np.float32).tobytes()),
        )
    conn.execute("INSERT INTO feedback (user_id, destination_id, action) VALUES (1, 'a', 'like')")
    conn.execute("INSERT INTO feedback (user_id, destination_id, action) VALUES (1, 'b', 'dislike')")
    conn.commit()

    first = load_feedback_bias(conn, 1)
    second = load_feedback_bias(conn, 1)

    assert first is not None
    assert abs(float(np.linalg.norm(first)) - 1.0) < 1e-5
    assert np.allclose(first, second)


class FakeRanker:
    def rank(self, recommendations, profile):
        for rank, rec in enumerate(recommendations, start=1):
            rec.rank = rank
            rec.explanation = f"stub for {rec.destination.name}"
        return recommendations


def _destination(name, country, attribute, lat=1.0, lon=1.0):
    return Destination(id=name, name=name, lat=lat, lon=lon, country=country, attributes=[attribute])


DESTINATIONS = [
    _destination("Coastland", "Croatia", "coastal", 44.0, 15.0),
    _destination("Peakville", "Greece", "mountain", 39.0, 22.0),
    _destination("Metropolis", "Malta", "city", 35.90, 14.51),
]


def test_rank_excludes_visited_and_bounds():
    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    recs = rank_destinations(
        taste, DESTINATIONS, _embed_text, exclude_countries=["Malta"], top_k=5
    )

    names = [r.destination.name for r in recs]
    assert "Metropolis" not in names
    assert names[0] == "Coastland"
    assert [r.rank for r in recs] == list(range(1, len(recs) + 1))


def test_rank_is_repeatable():
    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    first = [r.destination.id for r in rank_destinations(taste, DESTINATIONS, _embed_text)]
    second = [r.destination.id for r in rank_destinations(taste, DESTINATIONS, _embed_text)]
    assert first == second


def test_taste_embedding_normalized():
    vector = taste_embedding([np.array([1.0, 1.0], dtype=np.float32)])
    assert abs(float(np.linalg.norm(vector)) - 1.0) < 1e-6


def test_best_matching_facet_scores_destination():
    facets = [
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        np.array([0.0, 1.0, 0.0], dtype=np.float32),
    ]

    def embed_text(text):
        return np.array([0.0, 1.0, 0.0], dtype=np.float32)

    destination = Destination(id="d", name="D", lat=1, lon=1, country="X", description="")
    recs = rank_destinations(None, [destination], embed_text, taste_facets=facets)

    assert recs[0].embedding_score == 1.0  # matches the second facet, not the first


def test_rank_tracks_closest_trip_and_attributes():
    from wanderlens.core.models import Facet

    facets = [
        Facet(trip_id=1, label="Puglia, Italy", vector=np.array([1.0, 0.0, 0.0], dtype=np.float32)),
        Facet(trip_id=2, label="Malta", vector=np.array([0.0, 1.0, 0.0], dtype=np.float32)),
    ]

    def embed_text(text):
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    destination = Destination(
        id="d", name="Coastland", lat=1.0, lon=1.0, country="Greece", description="a coastal town"
    )
    tags = taste_attribute_weights({"coastal": 1.0})

    rec = rank_destinations(
        None,
        [destination],
        embed_text,
        taste_tags=tags,
        taste_facets=facets,
        visited_centers=[(0.0, 0.0)],
    )[0]

    assert rec.best_trip_id == 1
    assert rec.best_trip_label == "Puglia, Italy"
    assert rec.best_facet_similarity == 1.0
    assert rec.matched_attributes.get("coastal") == 1.0
    assert rec.nearest_trip_km is not None


def test_mmr_diversifies_near_duplicates():
    p = Destination(id="p", name="P", lat=1, lon=1, country="X")
    q = Destination(id="q", name="Q", lat=1, lon=1, country="X")
    r = Destination(id="r", name="R", lat=1, lon=1, country="X")
    vectors = {
        "p": np.array([0.9, 0.44, 0.0], dtype=np.float32),
        "q": np.array([0.9, 0.43, 0.0], dtype=np.float32),  # near-duplicate of p
        "r": np.array([0.0, 1.0, 0.0], dtype=np.float32),  # dissimilar
    }
    taste = np.array([1.0, 1.0, 0.0], dtype=np.float32)

    plain = rank_destinations(taste, [p, q, r], vectors=vectors, top_k=2)
    varied = rank_destinations(taste, [p, q, r], vectors=vectors, top_k=2, diversity=0.9)

    assert [x.destination.id for x in plain] == ["p", "q"]
    assert [x.destination.id for x in varied] == ["p", "r"]


def test_novelty_preference_biases_selection():
    a = Destination(id="a", name="A", lat=1, lon=1, country="X")
    b = Destination(id="b", name="B", lat=1, lon=1, country="X")
    vectors = {
        "a": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "b": np.array([1.0, 0.0, 0.0], dtype=np.float32),
    }
    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    popularity = {"a": 0.9, "b": 0.1}

    familiar = rank_destinations(
        taste, [a, b], vectors=vectors, top_k=1, novelty="familiar", popularity=popularity
    )
    uncommon = rank_destinations(
        taste, [a, b], vectors=vectors, top_k=1, novelty="uncommon", popularity=popularity
    )

    assert familiar[0].destination.id == "a"
    assert uncommon[0].destination.id == "b"


def test_ranking_order_unchanged_by_facet_identity():
    from wanderlens.core.models import Facet

    def embed_text(text):
        vector = np.zeros(3, dtype=np.float32)
        lowered = text.lower()
        if "coast" in lowered:
            vector[0] = 1.0
        if "mountain" in lowered:
            vector[1] = 1.0
        return vector / np.linalg.norm(vector) if vector.sum() else np.array([1.0, 0.0, 0.0], dtype=np.float32)

    vectors = [
        Facet(trip_id=0, label="A", vector=np.array([1.0, 0.0, 0.0], dtype=np.float32)),
        Facet(trip_id=1, label="B", vector=np.array([0.0, 1.0, 0.0], dtype=np.float32)),
    ]
    bare = [f.vector for f in vectors]

    with_facets = [r.destination.id for r in rank_destinations(None, DESTINATIONS, embed_text, taste_facets=vectors)]
    with_bare = [r.destination.id for r in rank_destinations(None, DESTINATIONS, embed_text, taste_facets=bare)]

    assert with_facets == with_bare


def test_taste_attribute_weights_canonicalizes_and_normalizes():
    weights = taste_attribute_weights({"turquoise water": 0.5, "coastal city": 0.5})
    assert {"water", "coastal", "city"} <= set(weights)
    assert abs(sum(weights.values()) - 1.0) < 1e-6


def test_attribute_match_overrides_equal_embeddings():
    def embed_text(text):
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    coastal = Destination(
        id="c", name="Seaside", lat=1, lon=1, country="Greece", description="a coastal seaside town"
    )
    inland = Destination(
        id="i", name="Inland", lat=1, lon=1, country="Spain", description="an inland city in the mountains"
    )
    tags = taste_attribute_weights({"coastal": 1.0})

    ranked = rank_destinations(taste, [inland, coastal], embed_text, taste_tags=tags, alpha=0.5)

    assert ranked[0].destination.name == "Seaside"
    assert ranked[0].attribute_score > ranked[1].attribute_score
    assert ranked[0].embedding_score is not None


def _config(tmp_path):
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=tmp_path / "catalog",
        vlm_provider="test",
        vlm_model="test",
        api_key=None,
    )


def _seed(tmp_path):
    config = _config(tmp_path)
    conn = connect(config.db_path)
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 0, NULL, NULL, 'Malta', 'Valletta', 35.90, 14.51)"
    )
    for i in range(3):
        conn.execute(
            "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, ?, 3, ?)",
            (f"p{i}", np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes()),
        )
        conn.execute(
            "INSERT INTO trip_photos (user_id, trip_id, photo_id) VALUES (1, 0, ?)", (f"p{i}",)
        )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (1, 'geography', 'Malta', 1.0)"
    )
    conn.execute(
        "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (1, 'subjects', 'coastal', 0.6)"
    )
    conn.commit()
    return config


def test_run_recommend_end_to_end(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    recs = run_recommend(
        config,
        count=5,
        embedder=FakeEmbedder(),
        catalog=catalog,
        ranker=FakeRanker(),
    )

    assert recs
    assert all(r.destination.country != "Malta" for r in recs)
    assert all(r.explanation.startswith("stub") for r in recs)
    assert recs[0].destination.name == "Coastland"

    conn = sqlite3.connect(config.db_path)
    stored = conn.execute("SELECT COUNT(*) FROM recommendations").fetchone()[0]
    assert stored == len(recs)

    row = conn.execute(
        "SELECT destination_name, destination_country, destination_lat, "
        "embedding_score, attribute_score FROM recommendations WHERE rank = 1"
    ).fetchone()
    assert row[0] == "Coastland"
    assert row[1] == "Croatia"
    assert row[2] == 44.0
    assert row[3] is not None
    assert row[4] is not None


def test_destination_embeddings_are_cached(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)
    embedder = CountingEmbedder()

    run_recommend(config, count=5, embedder=embedder, catalog=catalog)
    first = embedder.text_calls
    assert first == 2  # Metropolis (Malta) is excluded by proximity

    run_recommend(config, count=5, embedder=embedder, catalog=catalog)
    assert embedder.text_calls == first, "destination embeddings should be cached"


def test_run_recommend_without_embeddings_returns_empty(tmp_path):
    config = _config(tmp_path)
    conn = connect(config.db_path)
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.commit()

    assert run_recommend(config, embedder=FakeEmbedder(), catalog=JsonCatalog(DESTINATIONS)) == []


def test_run_recommend_fetches_and_caches_media(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)
    seen = {}

    def fake_fetcher(conn, recommendations, cfg):
        seen["count"] = len(recommendations)
        for rec in recommendations:
            conn.execute(
                "INSERT OR REPLACE INTO destination_media (destination_id, title, fetched_at) "
                "VALUES (?, ?, ?)",
                (rec.destination.id, "T", "now"),
            )
        conn.commit()
        return len(recommendations)

    recs = run_recommend(
        config,
        count=5,
        embedder=FakeEmbedder(),
        catalog=catalog,
        media=True,
        media_fetcher=fake_fetcher,
    )

    assert recs
    assert seen["count"] == len(recs)
    conn = connect(config.db_path)
    assert conn.execute("SELECT COUNT(*) FROM destination_media").fetchone()[0] == len(recs)


def test_run_recommend_survives_media_error(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    def boom(conn, recommendations, cfg):
        raise RuntimeError("media fetch failed")

    recs = run_recommend(
        config, embedder=FakeEmbedder(), catalog=catalog, media=True, media_fetcher=boom
    )

    assert recs


def test_run_recommend_persists_evidence(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    run_recommend(config, count=5, embedder=FakeEmbedder(), catalog=catalog)

    row = sqlite3.connect(config.db_path).execute(
        "SELECT best_trip_label, matched_attributes, nearest_trip_km "
        "FROM recommendations WHERE rank = 1"
    ).fetchone()
    assert row[0] == "Valletta, Malta"
    assert "coastal" in (row[1] or "")
    assert row[2] is not None


def test_run_recommend_explains_with_evidence(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    recs = run_recommend(config, embedder=FakeEmbedder(), catalog=catalog)

    assert "Valletta, Malta" in recs[0].explanation
    assert "coastal" in recs[0].explanation


class CountingExplainer:
    name = "stub"
    prompt_version = "v1"

    def __init__(self):
        self.calls = 0

    def synthesize(self, evidence):
        self.calls += 1
        return f"LLM why for {evidence['destination']}"


class RaisingExplainer:
    name = "boom"
    prompt_version = "v1"

    def synthesize(self, evidence):
        raise RuntimeError("no")


def test_explanation_synthesis_is_cached(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)
    explainer = CountingExplainer()

    run_recommend(config, embedder=FakeEmbedder(), catalog=catalog, explainer=explainer)
    first = explainer.calls
    assert first >= 1

    recs = run_recommend(
        config, embedder=FakeEmbedder(), catalog=catalog, explainer=explainer
    )
    assert explainer.calls == first, "cached explanation should be reused"
    assert recs[0].explanation.startswith("LLM why")


def test_synthesis_failure_falls_back(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    recs = run_recommend(
        config, embedder=FakeEmbedder(), catalog=catalog, explainer=RaisingExplainer()
    )

    assert recs
    assert recs[0].explanation


def test_run_recommend_persists_popularity(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    run_recommend(
        config,
        embedder=FakeEmbedder(),
        catalog=catalog,
        popularity=True,
        popularity_fetcher=lambda conn, dests: {d.id: 0.8 for d in dests},
    )

    row = sqlite3.connect(config.db_path).execute(
        "SELECT popularity, popularity_label FROM recommendations WHERE rank = 1"
    ).fetchone()
    assert row[0] == 0.8
    assert row[1] == "famous"


def test_run_recommend_survives_popularity_error(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    def boom(conn, dests):
        raise RuntimeError("pageviews unavailable")

    recs = run_recommend(
        config, embedder=FakeEmbedder(), catalog=catalog, popularity=True, popularity_fetcher=boom
    )

    assert recs


def test_default_alpha_is_calibrated():
    assert inspect.signature(rank_destinations).parameters["alpha"].default == 0.25


def test_rare_attribute_outranks_generic():
    def embed_text(text):
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    rare = Destination(
        id="rare", name="Glacier Bay", lat=1, lon=1, country="X", description="a glacier valley"
    )
    generic = Destination(
        id="generic", name="Coast Town", lat=1, lon=1, country="Y", description="a coastal town"
    )
    fillers = [
        Destination(
            id=f"c{i}", name=f"Coast{i}", lat=1, lon=1, country="Z", description="a coastal town"
        )
        for i in range(6)
    ]
    tags = taste_attribute_weights({"coastal": 1.0, "snow": 1.0})

    ranked = rank_destinations(
        taste, [generic, rare, *fillers], embed_text, taste_tags=tags
    )

    assert ranked[0].destination.id == "rare"


def test_closer_embedding_ranks_higher():
    a = Destination(id="a", name="A", lat=1, lon=1, country="X")
    b = Destination(id="b", name="B", lat=1, lon=1, country="X")
    vectors = {
        "a": np.array([1.0, 0.0, 0.0], dtype=np.float32),
        "b": np.array([0.0, 1.0, 0.0], dtype=np.float32),
    }
    taste = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    ranked = rank_destinations(
        taste, [b, a], vectors=vectors, taste_tags=taste_attribute_weights({"coastal": 1.0})
    )

    assert ranked[0].destination.id == "a"


def test_destination_attributes_drive_embedding_ranking():
    def embed_text(text):
        return np.array([1.0, 0.0] if "coastal" in text.lower() else [0.0, 1.0], dtype=np.float32)

    taste = np.array([1.0, 0.0], dtype=np.float32)
    with_attribute = Destination(id="a", name="Alpha", lat=1, lon=1, country="G", attributes=["coastal"])
    without = Destination(id="b", name="Beta", lat=1, lon=1, country="G")

    ranked = rank_destinations(taste, [without, with_attribute], embed_text)

    assert "coastal" in destination_text(with_attribute)
    assert ranked[0].destination.id == "a"


def test_thin_trip_facet_is_down_weighted(tmp_path):
    config = _seed(tmp_path)
    conn = connect(config.db_path)
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 1, NULL, NULL, 'Greece', 'Athens', 37.98, 23.72)"
    )
    for i in range(4):
        conn.execute(
            "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, ?, 3, ?)",
            (f"g{i}", np.array([0.0, 1.0, 0.0], dtype=np.float32).tobytes()),
        )
        conn.execute(
            "INSERT INTO trip_photos (user_id, trip_id, photo_id) VALUES (1, 1, ?)", (f"g{i}",)
        )
    conn.commit()

    facets = load_taste_facets(conn, 1, min_photos=4)
    weights = {facet.trip_id: facet.weight for facet in facets}

    assert weights[1] == 1.0, "four-photo trip keeps full weight"
    assert weights[0] == 0.75, "three-photo trip is down-weighted"


def test_run_recommend_survives_enricher_error(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    class Boom:
        model = "boom"
        prompt_version = "v1"

        def attribute_trip(self, tags, context=""):
            raise RuntimeError("no")

        def description(self, destination):
            raise RuntimeError("no")

    recs = run_recommend(config, embedder=FakeEmbedder(), catalog=catalog, enricher=Boom())

    assert recs

