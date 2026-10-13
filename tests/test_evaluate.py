import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.config import Config
from wanderlens.core.evaluate import evaluate_holdout, evaluate_resurfacing, mrr, precision_at_k
from wanderlens.core.models import Destination, Recommendation
from wanderlens.db import connect, init_db
from wanderlens.pipeline.evaluate import run_eval, run_synthetic_eval


def test_evaluate_holdout_reports_rank():
    destinations = [
        Destination(id="it", name="ItalyCoast", lat=1, lon=1, country="Italy"),
        Destination(id="gr", name="GreecePeak", lat=1, lon=1, country="Greece"),
    ]
    ranked = [
        Recommendation(destination=destinations[0], score=1.0, rank=1),
        Recommendation(destination=destinations[1], score=0.0, rank=2),
    ]
    result = evaluate_holdout(ranked, "Italy", within_top=5)
    assert result.passed and result.rank == 1
    assert "PASS" in result.describe()


def test_evaluate_resurfacing_uses_distance():
    near = Destination(id="n", name="Near", lat=35.90, lon=14.51, country="Malta")
    far = Destination(id="f", name="Far", lat=40.0, lon=22.0, country="Greece")
    ranked = [
        Recommendation(destination=far, score=0.9, rank=1),
        Recommendation(destination=near, score=0.1, rank=2),
    ]
    result = evaluate_resurfacing(ranked, (35.90, 14.51), radius_km=60, within_top=50, label="Valletta")
    assert result.passed and result.rank == 2
    assert "Valletta" in result.describe()


class FakeEmbedder:
    dim = 2

    def embed_text(self, text):
        return np.array([0.0, 1.0], dtype=np.float32)

    def embed_image(self, path):
        return np.array([0.0, 1.0], dtype=np.float32)


class FakeProvider:
    name = "stub"

    def describe(self, name, country):
        return "stub description"


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
    # two trips: Malta (coastal) and Greece (mountain)
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 0, NULL, NULL, 'Malta', 'Valletta', 35.90, 14.51)"
    )
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 1, NULL, NULL, 'Greece', 'Athens', 37.98, 23.72)"
    )
    for photo_id, trip_id, vec in [("p0", 0, [1.0, 0.0]), ("p1", 1, [0.0, 1.0])]:
        conn.execute(
            "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, ?, 2, ?)",
            (photo_id, np.array(vec, dtype=np.float32).tobytes()),
        )
        conn.execute(
            "INSERT INTO trip_photos (user_id, trip_id, photo_id) VALUES (1, ?, ?)",
            (trip_id, photo_id),
        )
    conn.execute("INSERT INTO trip_subjects (user_id, trip_id, subject) VALUES (1, 1, 'mountains')")
    conn.commit()
    return config


DESTINATIONS = [
    Destination(id="mt", name="MaltaTown", lat=35.90, lon=14.51, country="Malta", description="a coastal town"),
    Destination(id="gr", name="GreeceTown", lat=37.98, lon=23.72, country="Greece", description="a mountain town"),
]


def test_run_eval_holds_out_a_trip(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    text = run_eval(config, holdout="Valletta", embedder=FakeEmbedder(), catalog=catalog, providers=[FakeProvider()])

    assert "Valletta" in text
    assert "PASS" in text


def test_run_eval_rejects_non_visited_holdout(tmp_path):
    config = _seed(tmp_path)
    text = run_eval(config, holdout="France", embedder=FakeEmbedder(), catalog=JsonCatalog(DESTINATIONS), providers=[FakeProvider()])
    assert "not a visited trip" in text


def test_precision_at_k_perfect_partial_and_empty():
    assert precision_at_k(["a", "b", "c"], {"a", "b"}, 2) == 1.0
    assert abs(precision_at_k(["a", "x", "b"], {"a", "b"}, 3) - 2 / 3) < 1e-9
    assert precision_at_k(["x", "y"], {"a"}, 2) == 0.0
    assert precision_at_k(["a"], set(), 1) == 0.0


def test_mrr_values():
    assert mrr(["a"], {"a"}) == 1.0
    assert mrr(["x", "a"], {"a"}) == 0.5
    assert mrr(["x", "y"], {"a"}) == 0.0
    assert mrr(["a"], set()) == 0.0


def test_synthetic_eval_reports_metrics():
    text = run_synthetic_eval(k=3)
    assert "precision@3" in text
    assert "MRR" in text
    assert "precision@3 = 1.00" in text, text
    assert "MRR = 1.00" in text, text

