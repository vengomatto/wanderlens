from wanderlens.catalog.popularity import fetch_pageviews, fetch_popularity_for, is_cached
from wanderlens.core.models import Destination
from wanderlens.core.recommend import normalize_popularity, popularity_label
from wanderlens.db import connect, init_db


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return self.response


def test_fetch_pageviews_sums_items():
    session = FakeSession(FakeResponse({"items": [{"views": 100}, {"views": 150}]}))
    assert fetch_pageviews("Algarve", session=session) == 250


def test_fetch_pageviews_miss():
    assert fetch_pageviews("Nowhere", session=FakeSession(FakeResponse({}))) is None


def test_normalize_and_label():
    assert normalize_popularity(0) == 0.0
    assert normalize_popularity(None) is None
    assert popularity_label(None) == ""
    assert popularity_label(0.9) == "famous"
    assert popularity_label(0.5) == "balanced"
    assert popularity_label(0.1) == "uncommon"


def test_fetch_popularity_for_caches(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    destination = Destination(id="wv:A", name="Algarve", lat=1.0, lon=1.0)
    session = FakeSession(FakeResponse({"items": [{"views": 1_000_000}]}))

    scores = fetch_popularity_for(conn, [destination], session=session)
    assert "wv:A" in scores
    assert is_cached(conn, "wv:A")

    calls = session.calls
    fetch_popularity_for(conn, [destination], session=session)
    assert session.calls == calls, "cached popularity should not refetch"


def test_fetch_popularity_negative_is_cached(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    destination = Destination(id="wv:B", name="Nowhere", lat=1.0, lon=1.0)
    session = FakeSession(FakeResponse({}))

    scores = fetch_popularity_for(conn, [destination], session=session)
    assert scores == {}
    assert is_cached(conn, "wv:B")
    assert fetch_popularity_for(conn, [destination], session=session) == {}
