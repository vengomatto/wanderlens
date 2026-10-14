import numpy as np

from wanderlens.catalog.image_embeddings import ensure_destination_image_embeddings
from wanderlens.core.models import Destination, Facet
from wanderlens.core.recommend import rank_destinations
from wanderlens.db import connect, init_db


def _facet():
    return Facet(trip_id=0, label="trip 0", vector=np.array([1.0, 0.0], dtype=np.float32))


def test_image_vector_is_preferred_over_text():
    destination = Destination(id="d", name="D", lat=1, lon=1, country="X")
    text_vectors = {"d": np.array([0.0, 1.0], dtype=np.float32)}  # text orthogonal
    image_vectors = {"d": np.array([1.0, 0.0], dtype=np.float32)}  # image aligned

    with_image = rank_destinations(
        None, [destination], None, vectors=text_vectors, taste_facets=[_facet()],
        image_vectors=image_vectors,
    )[0]
    text_only = rank_destinations(
        None, [destination], None, vectors=text_vectors, taste_facets=[_facet()]
    )[0]

    assert with_image.embedding_score > 0.99
    assert text_only.embedding_score < 0.01


def test_text_fallback_when_no_image_vector():
    destination = Destination(id="d", name="D", lat=1, lon=1, country="X")
    text_vectors = {"d": np.array([1.0, 0.0], dtype=np.float32)}
    rec = rank_destinations(
        None, [destination], None, vectors=text_vectors, taste_facets=[_facet()],
        image_vectors={},
    )[0]
    assert rec.embedding_score > 0.99


class FakeEmbedder:
    dim = 2
    cache_key = "fake"

    def embed_image(self, path):
        return np.array([1.0, 0.0], dtype=np.float32)


class _Response:
    def __init__(self, content):
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        return None


class _Session:
    def get(self, url, **kwargs):
        return _Response(b"jpegdata")


def _conn(tmp_path):
    conn = connect(tmp_path / "i.sqlite3")
    init_db(conn)
    return conn


def test_image_embeddings_derived_and_cached(tmp_path):
    conn = _conn(tmp_path)
    destination = Destination(id="d", name="D", lat=1, lon=1, country="X")
    calls = {"n": 0}

    def fetch_urls(dest, session=None, limit=4):
        calls["n"] += 1
        return ["https://x.test/1.jpg", "https://x.test/2.jpg"]

    result = ensure_destination_image_embeddings(
        conn, [destination], FakeEmbedder(), fetch_urls=fetch_urls, session=_Session()
    )
    assert destination.id in result
    assert result[destination.id].shape == (2,)

    ensure_destination_image_embeddings(
        conn, [destination], FakeEmbedder(), fetch_urls=fetch_urls, session=_Session()
    )
    assert calls["n"] == 1, "cached destination should not refetch images"


def test_image_embeddings_tolerate_no_images(tmp_path):
    conn = _conn(tmp_path)
    destination = Destination(id="d", name="D", lat=1, lon=1, country="X")
    result = ensure_destination_image_embeddings(
        conn,
        [destination],
        FakeEmbedder(),
        fetch_urls=lambda dest, session=None, limit=4: [],
        session=_Session(),
    )
    assert result == {}
