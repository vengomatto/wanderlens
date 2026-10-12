import json

from wanderlens.catalog.fetch import (
    COMMONS_API,
    WIKIPEDIA_API,
    WIKIVOYAGE_API,
    fetch_commons_gallery,
    fetch_wikipedia_media,
)
from wanderlens.catalog.media import (
    CommonsMediaProvider,
    WikimediaMediaProvider,
    fetch_media,
    fetch_media_for,
    is_media_cached,
)
from wanderlens.catalog.regions import NOMINATIM_SEARCH
from wanderlens.core.models import Destination, Recommendation
from wanderlens.db import connect, init_db


class FakeResponse:
    def __init__(self, payload=None, content=b"", status=200):
        self._payload = payload
        self.content = content
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        for needle, response in self.routes.items():
            if needle in url:
                return response() if callable(response) else response
        return FakeResponse(status=404)


WIKI_JSON = {
    "query": {
        "pages": {
            "1": {
                "title": "Algarve",
                "extract": "Algarve is a region in southern Portugal known for its coast.",
                "fullurl": "https://en.wikipedia.org/wiki/Algarve",
                "thumbnail": {"source": "https://upload.test/hero.jpg"},
            }
        }
    }
}

COMMONS_JSON = {
    "query": {
        "pages": {
            "1": {
                "title": "File:C1.jpg",
                "imageinfo": [
                    {
                        "thumburl": "https://upload.test/c1.jpg",
                        "width": 1600,
                        "height": 1000,
                        "mime": "image/jpeg",
                        "extmetadata": {
                            "LicenseShortName": {"value": "CC BY-SA 4.0"},
                            "Artist": {"value": "<a href='#'>Jane Doe</a>"},
                        },
                    }
                ],
            }
        }
    }
}


def _destination():
    return Destination(id="wy:algarve", name="Algarve", lat=37.0, lon=-8.0, country="Portugal")


def test_fetch_wikipedia_media_parses():
    session = FakeSession({WIKIPEDIA_API: FakeResponse(WIKI_JSON)})
    data = fetch_wikipedia_media("Algarve", "Portugal", session=session)

    assert data["title"] == "Algarve"
    assert data["image_url"].endswith("hero.jpg")
    assert data["page_url"].endswith("/Algarve")
    assert "coast" in data["extract"]


def test_fetch_wikipedia_media_miss():
    session = FakeSession({WIKIPEDIA_API: FakeResponse({"query": {"pages": {}}})})
    assert fetch_wikipedia_media("Nowhere", session=session) is None


def test_fetch_commons_gallery_strips_html_and_reads_license():
    session = FakeSession({COMMONS_API: FakeResponse(COMMONS_JSON)})
    images = fetch_commons_gallery(37.0, -8.0, session=session)

    assert len(images) == 1
    assert images[0]["url"].endswith("c1.jpg")
    assert images[0]["license"] == "CC BY-SA 4.0"
    assert images[0]["attribution"] == "Jane Doe"


def test_wikimedia_provider_builds_bundle():
    session = FakeSession({WIKIPEDIA_API: FakeResponse(WIKI_JSON), COMMONS_API: FakeResponse(COMMONS_JSON)})
    media = WikimediaMediaProvider(session=session).fetch(_destination())

    assert media is not None
    assert media.extract
    assert media.page_url.endswith("/Algarve")
    assert [i.url for i in media.images] == [
        "https://upload.test/hero.jpg",
        "https://upload.test/c1.jpg",
    ]


def test_fetch_media_caches_files_and_rows(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse(COMMONS_JSON),
            NOMINATIM_SEARCH: FakeResponse([{"geojson": {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]}}]),
            "upload.test": FakeResponse(content=b"jpegdata"),
        }
    )
    media_dir = tmp_path / "media"

    assert fetch_media(conn, _destination(), media_dir, session=session) is True

    row = conn.execute("SELECT region_kind, extract FROM destination_media").fetchone()
    assert row["region_kind"] == "precise"
    assert row["extract"]
    files = sorted(p.name for p in media_dir.iterdir())
    assert len(files) == 2
    images = conn.execute("SELECT position, filename FROM destination_images ORDER BY position").fetchall()
    assert [i["position"] for i in images] == [0, 1]


def test_fetch_media_second_call_is_cached(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse(COMMONS_JSON),
            NOMINATIM_SEARCH: FakeResponse([]),
            "upload.test": FakeResponse(content=b"jpegdata"),
        }
    )
    media_dir = tmp_path / "media"

    fetch_media(conn, _destination(), media_dir, session=session)
    calls = len(session.calls)

    assert fetch_media(conn, _destination(), media_dir, session=session) is False
    assert len(session.calls) == calls
    assert is_media_cached(conn, "wy:algarve")


def test_fetch_media_records_negative_result(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse({"query": {"pages": {}}}),
            COMMONS_API: FakeResponse({"query": {"pages": {}}}),
            NOMINATIM_SEARCH: FakeResponse([]),
        }
    )

    assert fetch_media(conn, _destination(), tmp_path / "media", session=session) is True
    assert is_media_cached(conn, "wy:algarve")
    assert conn.execute("SELECT COUNT(*) FROM destination_images").fetchone()[0] == 0
    assert fetch_media(conn, _destination(), tmp_path / "media", session=session) is False


class RaisingProvider:
    name = "boom"

    def fetch(self, destination):
        raise RuntimeError("provider exploded")


def test_chain_falls_through_on_error(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession({"upload.test": FakeResponse(content=b"jpegdata")})
    chain = [RaisingProvider(), CommonsMediaProvider(session=session)]

    fetch_media(conn, _destination(), tmp_path / "media", chain=chain, session=session)
    # Commons provider needs a session returning gallery; without COMMONS route it misses.
    # The run must still complete and cache a (negative) row rather than raise.
    assert is_media_cached(conn, "wy:algarve")


WIKIVOYAGE_PAGE = {
    "query": {
        "pages": {
            "1": {
                "title": "Algarve",
                "fullurl": "https://en.wikivoyage.org/wiki/Algarve",
                "extract": "TRAVEL PROSE about the Algarve.",
                "pageprops": {},
                "extlinks": [],
                "links": [],
            }
        }
    }
}


def test_media_prefers_travel_extract(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIVOYAGE_API: FakeResponse(WIKIVOYAGE_PAGE),
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse({"query": {"pages": {}}}),
            NOMINATIM_SEARCH: FakeResponse([]),
        }
    )

    fetch_media(conn, _destination(), tmp_path / "media", session=session)

    row = conn.execute("SELECT extract FROM destination_media").fetchone()
    assert row["extract"].startswith("TRAVEL PROSE")


def test_gallery_reaches_ten(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    many = {
        "query": {
            "pages": {
                str(i): {
                    "title": f"File:G{i}.jpg",
                    "imageinfo": [
                        {
                            "thumburl": f"https://upload.test/g{i}.jpg",
                            "width": 1600,
                            "height": 1000,
                            "mime": "image/jpeg",
                            "extmetadata": {},
                        }
                    ],
                }
                for i in range(12)
            }
        }
    }
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse(many),
            NOMINATIM_SEARCH: FakeResponse([]),
            "upload.test": FakeResponse(content=b"x"),
        }
    )

    fetch_media(conn, _destination(), tmp_path / "media", session=session)

    assert conn.execute("SELECT COUNT(*) FROM destination_images").fetchone()[0] >= 10


def test_image_downloads_send_user_agent(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse(COMMONS_JSON),
            NOMINATIM_SEARCH: FakeResponse([]),
            "upload.test": FakeResponse(content=b"jpegdata"),
        }
    )

    fetch_media(conn, _destination(), tmp_path / "media", session=session)

    image_calls = [call for call in session.calls if "upload.test" in call[0]]
    assert image_calls
    for _, kwargs in image_calls:
        assert kwargs.get("headers", {}).get("User-Agent")


def test_fetch_media_for_is_best_effort(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = FakeSession(
        {
            WIKIPEDIA_API: FakeResponse(WIKI_JSON),
            COMMONS_API: FakeResponse(COMMONS_JSON),
            NOMINATIM_SEARCH: FakeResponse([]),
            "upload.test": FakeResponse(content=b"jpegdata"),
        }
    )
    recs = [
        Recommendation(destination=_destination(), score=0.9, rank=1),
        Recommendation(destination=Destination(id="x", name="X", lat=1.0, lon=1.0), score=0.5, rank=2),
    ]

    stored = fetch_media_for(conn, recs, tmp_path / "media", session=session)
    assert stored == 2
