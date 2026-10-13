from wanderlens.catalog.media import OpenverseMediaProvider, filter_images
from wanderlens.core.models import Destination


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
