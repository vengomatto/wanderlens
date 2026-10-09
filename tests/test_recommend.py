import sqlite3

import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.config import Config
from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations, taste_embedding
from wanderlens.db import connect, init_db
from wanderlens.pipeline.recommend import run_recommend


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


class FakeRanker:
    def rank(self, recommendations, profile):
        for rank, rec in enumerate(recommendations, start=1):
            rec.rank = rank
            rec.explanation = f"stub for {rec.destination.name}"
        return recommendations


def _destination(name, country, attribute):
    return Destination(id=name, name=name, lat=1.0, lon=1.0, country=country, attributes=[attribute])


DESTINATIONS = [
    _destination("Coastland", "Croatia", "coastal"),
    _destination("Peakville", "Greece", "mountain"),
    _destination("Metropolis", "Malta", "city"),
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
    for i in range(3):
        conn.execute(
            "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, ?, 3, ?)",
            (f"p{i}", np.array([1.0, 0.0, 0.0], dtype=np.float32).tobytes()),
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


def test_destination_embeddings_are_cached(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)
    embedder = CountingEmbedder()

    run_recommend(config, count=5, embedder=embedder, catalog=catalog)
    first = embedder.text_calls
    assert first == len(DESTINATIONS)

    run_recommend(config, count=5, embedder=embedder, catalog=catalog)
    assert embedder.text_calls == first, "destination embeddings should be cached"


def test_run_recommend_without_embeddings_returns_empty(tmp_path):
    config = _config(tmp_path)
    conn = connect(config.db_path)
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.commit()

    assert run_recommend(config, embedder=FakeEmbedder(), catalog=JsonCatalog(DESTINATIONS)) == []
