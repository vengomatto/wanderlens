from pathlib import Path

from wanderlens.catalog.destinations import JsonCatalog, destination_from_dict, destination_to_dict
from wanderlens.catalog.wikivoyage import build_country_destinations, country_destination_titles
from wanderlens.config import Config
from wanderlens.core.models import Destination
from wanderlens.pipeline.recommend import build_catalog_for

WIKITEXT = """
== Regions ==
* [[Catalonia]]
* [[Andalusia]]
== Cities ==
* [[Madrid]]
== Other destinations ==
* [[Costa del Sol]]
* [[File:Beach.jpg|thumb|a beach]]
"""

CITIES = (
    "3120514\tMadrid\tMadrid\t\t40.4165\t-3.7026\tP\tPPLC\tES\t\t\t\t\t\t3255944\tn/a\t\tEurope/Madrid\t2023-01-01\n"
)
COUNTRIES = "ES\tESP\t724\tES\tSpain\tMadrid\t47351567\tEurope\tSpain\tEUR\tEuro\t+34\t.es\tES\t^\n"


class _Response:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


class WikiSession:
    def __init__(self, wikitext, pages):
        self.wikitext = wikitext
        self.pages = pages

    def get(self, url, params=None, **kwargs):
        if params and params.get("action") == "parse":
            return _Response({"parse": {"wikitext": {"*": self.wikitext}}})
        return _Response({"query": {"pages": self.pages}})


def test_country_destination_titles_parses_sections():
    pairs = country_destination_titles(WIKITEXT)
    assert ("Catalonia", "region") in pairs
    assert ("Madrid", "city") in pairs
    assert ("Costa del Sol", "other") in pairs
    assert all("File:" not in title for title, _ in pairs)


def test_build_country_destinations_with_coordinates():
    pages = {
        "1": {"title": "Madrid", "coordinates": [{"lat": 40.4, "lon": -3.7}], "extract": "The capital."},
        "2": {"title": "Costa del Sol", "coordinates": [{"lat": 36.5, "lon": -4.9}], "extract": "A coastal region."},
        "3": {"title": "Catalonia"},  # no coordinates -> skipped
    }
    session = WikiSession(WIKITEXT, pages)

    destinations = build_country_destinations("Spain", session=session)

    by_name = {d.name: d for d in destinations}
    assert set(by_name) == {"Madrid", "Costa del Sol"}
    assert by_name["Costa del Sol"].granularity == "other"
    assert by_name["Costa del Sol"].description == "A coastal region."
    assert by_name["Madrid"].granularity == "city"


def test_destination_round_trip_keeps_granularity():
    original = Destination(id="wv:X", name="X", lat=1.0, lon=2.0, country="Spain", granularity="region")
    assert destination_from_dict(destination_to_dict(original)).granularity == "region"


class StubProvider:
    name = "stub"

    def describe(self, name, country):
        return "stub"


def _config(tmp_path, source):
    catalog = tmp_path / "catalog"
    catalog.mkdir(parents=True, exist_ok=True)
    (catalog / "cities500.txt").write_text(CITIES)
    (catalog / "countryInfo.txt").write_text(COUNTRIES)
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=catalog,
        vlm_provider="t",
        vlm_model="t",
        api_key=None,
        catalog_source=source,
    )


def test_build_catalog_for_prefers_wikivoyage(tmp_path, monkeypatch):
    config = _config(tmp_path, "wikivoyage")
    monkeypatch.setattr(
        "wanderlens.catalog.wikivoyage.build_wikivoyage_catalog",
        lambda countries, **kwargs: JsonCatalog(
            [Destination(id="wv:Costa del Sol", name="Costa del Sol", lat=36.5, lon=-4.9, country="Spain", granularity="other")]
        ),
    )
    catalog = build_catalog_for(config, ["ES"], "dest.json")
    assert [d.name for d in catalog.candidates()] == ["Costa del Sol"]


def test_build_catalog_for_falls_back_to_geonames(tmp_path, monkeypatch):
    config = _config(tmp_path, "wikivoyage")
    monkeypatch.setattr(
        "wanderlens.catalog.wikivoyage.build_wikivoyage_catalog",
        lambda countries, **kwargs: JsonCatalog([]),
    )
    catalog = build_catalog_for(config, ["ES"], "dest.json", providers=[StubProvider()])
    assert [d.name for d in catalog.candidates()] == ["Madrid"]
