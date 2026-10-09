import numpy as np

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.config import Config
from wanderlens.core.evaluate import evaluate_holdout
from wanderlens.core.models import Destination, Recommendation
from wanderlens.db import connect, init_db
from wanderlens.pipeline.evaluate import run_eval


def _embed_text(text):
    lowered = text.lower()
    return np.array([1.0, 0.0], dtype=np.float32) if "coast" in lowered else np.array([0.0, 1.0], dtype=np.float32)


class FakeEmbedder:
    dim = 2

    def embed_text(self, text):
        return _embed_text(text)


DESTINATIONS = [
    Destination(id="it", name="ItalyCoast", lat=1, lon=1, country="Italy", attributes=["coastal"]),
    Destination(id="mt", name="MaltaCoast", lat=1, lon=1, country="Malta", attributes=["coastal"]),
    Destination(id="gr", name="GreecePeak", lat=1, lon=1, country="Greece", attributes=["mountain"]),
]


def test_evaluate_holdout_reports_rank():
    ranked = [
        Recommendation(destination=DESTINATIONS[0], score=1.0, rank=1),
        Recommendation(destination=DESTINATIONS[2], score=0.0, rank=2),
    ]
    result = evaluate_holdout(ranked, "Italy", within_top=5)
    assert result.passed
    assert result.rank == 1
    assert "PASS" in result.describe()


def test_evaluate_holdout_missing():
    result = evaluate_holdout([], "Italy", within_top=5)
    assert not result.passed
    assert "did not resurface" in result.describe()


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
        "INSERT INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (1, 'p1', 2, ?)",
        (np.array([1.0, 0.0], dtype=np.float32).tobytes(),),
    )
    for country in ("Italy", "Malta"):
        conn.execute(
            "INSERT INTO profile_entries (user_id, factor, key, value) VALUES (1, 'geography', ?, 0.5)",
            (country,),
        )
    conn.commit()
    return config


def test_run_eval_holds_out_and_excludes_remaining(tmp_path):
    config = _seed(tmp_path)
    catalog = JsonCatalog(DESTINATIONS)

    text = run_eval(config, holdout="Italy", embedder=FakeEmbedder(), catalog=catalog)

    assert "Italy" in text
    assert "PASS" in text


def test_run_eval_rejects_non_visited_holdout(tmp_path):
    config = _seed(tmp_path)
    text = run_eval(config, holdout="France", embedder=FakeEmbedder(), catalog=JsonCatalog(DESTINATIONS))
    assert "not a visited place" in text
