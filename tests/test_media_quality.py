from io import BytesIO

from PIL import Image

from wanderlens.catalog.media import (
    OpenverseMediaProvider,
    _average_hash,
    _hamming,
    fetch_media,
    filter_images,
)
from wanderlens.core.models import Destination, DestinationMedia, MediaImage
from wanderlens.db import connect, init_db


def _img(title, width=1600, height=1200, mime="image/jpeg", categories="", url=None):
    return {
        "title": title,
        "url": url or f"https://upload.test/{title}",
        "width": width,
        "height": height,
        "mime": mime,
        "categories": categories,
        "license": "CC BY-SA",
        "attribution": "Someone",
        "source": "commons",
    }


def test_assessed_images_come_first():
    plain = _img("File:Plain.jpg", width=3000)
    quality = _img("File:Quality.jpg", width=1200, categories="Quality images|Portugal")

    kept = filter_images([plain, quality])

    assert kept[0]["title"] == "File:Quality.jpg"


def test_landscape_preferred_over_portrait():
    portrait = _img("File:Portrait.jpg", width=1000, height=1800)
    landscape = _img("File:Landscape.jpg", width=1200, height=800)

    kept = filter_images([portrait, landscape])

    assert kept[0]["title"] == "File:Landscape.jpg"


def test_low_resolution_and_icons_dropped():
    low = _img("File:Low.jpg", width=400)
    icon = _img("File:Site icon.png", width=1600)

    assert filter_images([low, icon]) == []


def test_deduplicated_by_title():
    a = _img("File:Same.jpg")
    b = _img("File:Same.jpg", url="https://other.test/same.jpg")

    assert len(filter_images([a, b])) == 1


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _Session:
    def get(self, url, **kwargs):
        return _Response(
            {
                "results": [
                    {
                        "url": "https://o.test/1.jpg",
                        "title": "Kotor",
                        "filetype": "jpg",
                        "width": 2000,
                        "height": 1200,
                        "license": "cc0",
                        "creator": "X",
                    }
                ]
            }
        )


def test_openverse_provider_parses_and_maps_mime():
    destination = Destination(id="kotor", name="Kotor", lat=42.4, lon=18.7, country="Montenegro")

    images = OpenverseMediaProvider(session=_Session()).images(destination)

    assert images[0]["url"] == "https://o.test/1.jpg"
    assert images[0]["mime"] == "image/jpeg"
    assert images[0]["source"] == "openverse"
    assert images[0]["width"] == 2000


def _jpeg(color=(10, 20, 30)):
    buffer = BytesIO()
    Image.new("RGB", (64, 64), color).save(buffer, "JPEG")
    return buffer.getvalue()


class _BytesResponse:
    def __init__(self, content):
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {}


class _BytesSession:
    def __init__(self, content):
        self.content = content
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return _BytesResponse(self.content)


class _FakeProvider:
    name = "fake"

    def __init__(self, images):
        self._images = images

    def fetch(self, destination):
        return DestinationMedia(destination_id=destination.id, images=self._images)


def test_average_hash_is_stable_and_hamming_detects_dupes():
    a = _average_hash(_jpeg((10, 20, 30)))
    b = _average_hash(_jpeg((10, 20, 30)))
    c = _average_hash(_jpeg((200, 10, 10)))

    assert _hamming(a, b) == 0
    assert _hamming(a, c) >= 0


def test_fetch_media_refresh_rebuilds_cache(tmp_path):
    conn = connect(tmp_path / "m.sqlite3")
    init_db(conn)
    destination = Destination(id="d", name="D", lat=1.0, lon=1.0, country="X")
    chain = [_FakeProvider([MediaImage(url="https://x.test/1.jpg")])]
    session = _BytesSession(_jpeg())

    assert fetch_media(conn, destination, tmp_path, chain=chain, session=session) is True
    assert fetch_media(conn, destination, tmp_path, chain=chain, session=session) is False
    assert fetch_media(conn, destination, tmp_path, chain=chain, session=session, refresh=True) is True


def test_perceptual_dedupe_keeps_one(tmp_path):
    conn = connect(tmp_path / "m.sqlite3")
    init_db(conn)
    destination = Destination(id="d", name="D", lat=1.0, lon=1.0, country="X")
    chain = [
        _FakeProvider(
            [
                MediaImage(url="https://x.test/1.jpg"),
                MediaImage(url="https://x.test/2.jpg"),
            ]
        )
    ]
    session = _BytesSession(_jpeg())  # identical bytes for both URLs

    fetch_media(conn, destination, tmp_path, chain=chain, session=session)

    stored = conn.execute("SELECT COUNT(*) FROM destination_images").fetchone()[0]
    assert stored == 1
