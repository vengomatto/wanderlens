from wanderlens.catalog.fetch import (
    COMMONS_API,
    WIKIDATA_API,
    WIKIPEDIA_API,
    WIKIVOYAGE_API,
    fetch_commons_category,
    fetch_commons_imageinfo,
    fetch_wikipedia_article_images,
    fetch_wikidata_item_image,
)
from wanderlens.catalog.media import WikimediaMediaProvider, filter_images
from wanderlens.core.models import Destination


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
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def get(self, url, **kwargs):
        params = kwargs.get("params") or {}
        self.calls.append((url, params))
        return self.handler(url, params) or FakeResponse(status=404)


def _image(title, url, width=1600, mime="image/jpeg"):
    return {"title": title, "imageinfo": [{"thumburl": url, "width": width, "height": 900, "mime": mime, "extmetadata": {}}]}


def test_filter_images_drops_icons_lowres_and_duplicates():
    images = [
        {"title": "File:Beach.jpg", "mime": "image/jpeg", "width": 1600, "url": "a"},
        {"title": "File:Icon flag.svg", "mime": "image/svg+xml", "width": 1600, "url": "b"},
        {"title": "File:Map of X.png", "mime": "image/png", "width": 2000, "url": "c"},
        {"title": "File:Small.jpg", "mime": "image/jpeg", "width": 300, "url": "d"},
        {"title": "File:Beach.jpg", "mime": "image/jpeg", "width": 1600, "url": "a"},
    ]
    assert [i["url"] for i in filter_images(images)] == ["a"]


def test_fetch_commons_imageinfo_reads_size_and_mime():
    session = FakeSession(lambda url, params: FakeResponse({"query": {"pages": {"1": _image("File:C1.jpg", "u/c1.jpg")}}}))
    images = fetch_commons_imageinfo(["File:C1.jpg"], session=session)
    assert images[0]["width"] == 1600
    assert images[0]["mime"] == "image/jpeg"


def test_fetch_wikipedia_article_images():
    payload = {"query": {"pages": {"1": {"title": "Algarve", "images": [{"title": "File:A.jpg"}, {"title": "File:B.jpg"}]}}}}
    session = FakeSession(lambda url, params: FakeResponse(payload))
    assert fetch_wikipedia_article_images("Algarve", session=session) == ["File:A.jpg", "File:B.jpg"]


def test_fetch_commons_category():
    session = FakeSession(lambda url, params: FakeResponse({"query": {"pages": {"10": _image("File:Cat1.jpg", "u/cat1.jpg")}}}))
    images = fetch_commons_category("Category:Algarve", session=session)
    assert images[0]["url"] == "u/cat1.jpg"


def test_fetch_wikidata_item_image_resolves_p18():
    def handler(url, params):
        if WIKIDATA_API in url:
            return FakeResponse({"entities": {"Q1": {"claims": {"P18": [{"mainsnak": {"datavalue": {"value": "Lead.jpg"}}}]}}}})
        if COMMONS_API in url and params.get("titles"):
            return FakeResponse({"query": {"pages": {"1": _image("File:Lead.jpg", "u/lead.jpg")}}})
        return FakeResponse(status=404)

    images = fetch_wikidata_item_image("Q1", session=FakeSession(handler))
    assert images[0]["url"] == "u/lead.jpg"


def _curated_handler():
    def handler(url, params):
        if WIKIDATA_API in url:
            return FakeResponse(
                {"entities": {"Q1": {"claims": {
                    "P18": [{"mainsnak": {"datavalue": {"value": "Lead.jpg"}}}],
                    "P373": [{"mainsnak": {"datavalue": {"value": "Algarve"}}}],
                }}}}
            )
        if WIKIVOYAGE_API in url and params.get("action") == "query":
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "fullurl": "wv/Algarve", "extract": "prose", "pageprops": {"wikibase_item": "Q1"}, "extlinks": [], "links": []}}}})
        if WIKIPEDIA_API in url and params.get("prop") == "images":
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "images": [{"title": "File:Art1.jpg"}]}}}})
        if WIKIPEDIA_API in url:
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "fullurl": "wp/Algarve", "extract": "extract"}}}})
        if COMMONS_API in url and params.get("generator") == "categorymembers":
            return FakeResponse({"query": {"pages": {"10": _image("File:Cat1.jpg", "u/cat1.jpg")}}})
        if COMMONS_API in url and params.get("titles"):
            titles = params["titles"].split("|")
            pages = {str(i): _image(t, "u/" + t.split(":", 1)[1].lower()) for i, t in enumerate(titles)}
            return FakeResponse({"query": {"pages": pages}})
        return FakeResponse(status=404)

    return handler


def test_provider_assembles_curated_gallery_hero_first():
    session = FakeSession(_curated_handler())
    media = WikimediaMediaProvider(session=session).fetch(
        Destination(id="wv:Algarve", name="Algarve", lat=37.0, lon=-8.0, country="Portugal")
    )

    assert media is not None
    urls = [image.url for image in media.images]
    assert urls[0] == "u/lead.jpg"  # Wikidata P18 leads
    assert "u/art1.jpg" in urls  # article media
    assert "u/cat1.jpg" in urls  # Commons category


def test_provider_uses_fallback_only_when_few():
    def handler(url, params):
        if WIKIVOYAGE_API in url and params.get("action") == "query":
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "extract": "prose", "pageprops": {}, "extlinks": [], "links": []}}}})
        if WIKIPEDIA_API in url and params.get("prop") == "images":
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "images": []}}}})
        if WIKIPEDIA_API in url:
            return FakeResponse({"query": {"pages": {"1": {"title": "Algarve", "extract": "extract"}}}})
        if COMMONS_API in url and params.get("generator") == "geosearch":
            pages = {str(i): _image(f"File:N{i}.jpg", f"u/n{i}.jpg") for i in range(6)}
            return FakeResponse({"query": {"pages": pages}})
        if COMMONS_API in url:
            return FakeResponse({"query": {"pages": {}}})
        return FakeResponse(status=404)

    session = FakeSession(handler)
    media = WikimediaMediaProvider(session=session).fetch(
        Destination(id="wv:Algarve", name="Algarve", lat=37.0, lon=-8.0, country="Portugal")
    )
    assert len(media.images) >= 6
    assert any("n0.jpg" in image.url for image in media.images)
