from pathlib import Path

import numpy as np

from wanderlens.catalog.fetch import (
    enrich_records,
    fetch_wikidata_description,
    fetch_wikipedia_summary,
)
from wanderlens.config import Config
from wanderlens.core.models import Destination
from wanderlens.core.recommend import rank_destinations
from wanderlens.pipeline.recommend import default_catalog

CITIES = (
    "3170647\tGenoa\tGenoa\t\t44.40478\t8.94439\tP\tPPLA\tIT\t\t\t\t\t\t580000\tn/a\t\tEurope/Rome\t2023-01-01\n"
    "3169070\tRome\tRome\t\t41.89193\t12.51133\tP\tPPLA\tIT\t\t\t\t\t\t2318895\tn/a\t\tEurope/Rome\t2023-01-01\n"
    "2562305\tBirkirkara\tBirkirkara\t\t35.897\t14.461\tP\tPPL\tMT\t\t\t\t\t\t21676\tn/a\t\tEurope/Malta\t2023-01-01\n"
)
COUNTRIES = (
    "IT\tITA\t380\tIT\tItaly\tRome\t60360000\tEurope\tItaly\tEUR\tEuro\t+39\t.it\tIT\t^\n"
    "MT\tMLT\t470\tMT\tMalta\tValletta\t316000\tEurope\tMalta\tEUR\tEuro\t+356\t.mt\tMT\t^\n"
)


class _Response:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, data):
        self.data = data
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return _Response(self.data)


class OsmSession:
    def __init__(self, geocode, overpass):
        self.geocode = geocode
        self.overpass = overpass

    def get(self, url, **kwargs):
        return _Response(self.geocode)

    def post(self, url, **kwargs):
        return _Response(self.overpass)


def test_fetch_wikipedia_summary_parses():
    session = FakeSession(
        {"query": {"pages": {"1": {"title": "Cartagena, Spain", "extract": "Cartagena is a coastal city in Spain. It has a port."}}}}
    )
    summary = fetch_wikipedia_summary("Cartagena", "Spain", session=session)
    assert summary.startswith("Cartagena is a coastal city")
    assert session.calls == 1


def test_fetch_wikidata_description_parses():
    session = FakeSession({"search": [{"description": "municipality in the Region of Murcia, Spain"}]})
    assert fetch_wikidata_description("Cartagena", session=session) == "municipality in the Region of Murcia, Spain"


class StubProvider:
    name = "stub"

    def __init__(self, fn):
        self.fn = fn
        self.calls = 0

    def describe(self, name, country):
        self.calls += 1
        return self.fn(name, country)


def test_enrich_records_sets_description_and_tolerates_failure():
    records = [{"name": "A", "description": ""}, {"name": "B", "description": ""}]

    def flaky(name, country):
        if name == "B":
            raise RuntimeError("network")
        return "coastal town"

    enrich_records(records, providers=[StubProvider(flaky)])

    assert records[0]["description"] == "coastal town"
    assert records[1]["description"] == ""


def test_provider_chain_first_nonempty_wins():
    first = StubProvider(lambda name, country: "")
    second = StubProvider(lambda name, country: "from second")
    third = StubProvider(lambda name, country: "from third")

    records = [{"name": "X", "description": ""}]
    enrich_records(records, providers=[first, second, third])

    assert records[0]["description"] == "from second"
    assert first.calls == 1 and second.calls == 1 and third.calls == 0


def test_provider_chain_falls_back_on_exception():
    def boom(name, country):
        raise RuntimeError("down")

    records = [{"name": "X", "description": ""}]
    enrich_records(records, providers=[StubProvider(boom), StubProvider(lambda n, c: "ok")])

    assert records[0]["description"] == "ok"


def test_llm_provider_parses_and_handles_miss():
    from wanderlens.catalog.providers import LlmProvider

    class Model:
        def __init__(self, text): self.text = text
        def complete(self, prompt): return self.text

    assert LlmProvider(Model("a coastal town.")).describe("X", "Y") == "a coastal town."
    assert LlmProvider(Model("   ")).describe("X", "Y") is None

    class Broken:
        def complete(self, prompt): raise RuntimeError("no key")

    assert LlmProvider(Broken()).describe("X", "Y") is None


def test_build_provider_chain_respects_order():
    from wanderlens.catalog.providers import build_provider_chain
    from wanderlens.config import Config

    config = Config(
        data_dir=Path("."), photos_dir=Path("."), db_path=Path("."), catalog_path=Path("."),
        vlm_provider="t", vlm_model="t", api_key="k", description_providers=["llm", "wikimedia"],
    )
    chain = build_provider_chain(config)
    assert [p.name for p in chain] == ["llm", "wikimedia"]


def test_build_provider_chain_default_includes_osm():
    from wanderlens.catalog.providers import build_provider_chain
    from wanderlens.config import Config

    config = Config(
        data_dir=Path("."), photos_dir=Path("."), db_path=Path("."), catalog_path=Path("."),
        vlm_provider="t", vlm_model="t", api_key="k",
    )
    assert [p.name for p in build_provider_chain(config)] == ["wikimedia", "openstreetmap", "llm"]


def test_osm_provider_maps_features():
    from wanderlens.catalog.providers import OsmProvider

    overpass = {
        "elements": [
            {"tags": {"natural": "coastline"}},
            {"tags": {"harbour": "yes"}},
            {"tags": {"historic": "castle"}},
        ]
    }
    session = OsmSession([{"lat": "42.42", "lon": "18.77"}], overpass)
    text = OsmProvider(session=session, delay=0).describe("Kotor", "Montenegro")

    assert text and "coastal" in text and "marina" in text and "history" in text


def test_osm_provider_returns_none_when_missing():
    from wanderlens.catalog.providers import OsmProvider

    assert OsmProvider(session=OsmSession([], {}), delay=0).describe("Nowhere", "X") is None


def _config(tmp_path):
    catalog = tmp_path / "catalog"
    catalog.mkdir(parents=True, exist_ok=True)
    (catalog / "cities500.txt").write_text(CITIES)
    (catalog / "countryInfo.txt").write_text(COUNTRIES)
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=catalog,
        vlm_provider="test",
        vlm_model="test",
        api_key=None,
    )


def test_default_catalog_enriches_then_caches(tmp_path):
    config = _config(tmp_path)
    provider = StubProvider(lambda name, country: f"coastal town near {name}")

    first = default_catalog(config, providers=[provider])
    assert {d.name for d in first.candidates()} == {"Genoa", "Rome"}
    assert all(d.description for d in first.candidates())
    assert provider.calls == 2

    second = default_catalog(config, providers=[provider])
    assert provider.calls == 2, "cache should prevent refetching"
    assert {d.name for d in second.candidates()} == {"Genoa", "Rome"}


def test_country_code_for_name(tmp_path):
    config = _config(tmp_path)
    from wanderlens.catalog.fetch import country_code_for_name

    assert country_code_for_name(config.catalog_path / "countryInfo.txt", "Malta") == "MT"
    assert country_code_for_name(config.catalog_path / "countryInfo.txt", "Wakanda") is None


def test_eval_catalog_includes_holdout_country(tmp_path):
    config = _config(tmp_path)
    from wanderlens.pipeline.evaluate import _eval_catalog

    catalog = _eval_catalog(config, "Malta", providers=[StubProvider(lambda n, c: "desc")])

    countries = {d.country for d in catalog.candidates()}
    assert "Malta" in countries, "hold-out country must be present as candidates"
    assert "Italy" in countries


def test_described_destination_ranks_above_undescribed():
    def embed_text(text):
        return np.array([1.0, 0.0] if "coast" in text.lower() else [0.0, 1.0], dtype=np.float32)

    taste = np.array([1.0, 0.0], dtype=np.float32)
    described = Destination(id="a", name="Alpha", lat=1, lon=1, country="Greece", description="a coastal town")
    plain = Destination(id="b", name="Beta", lat=1, lon=1, country="Greece", description="")

    ranked = rank_destinations(taste, [plain, described], embed_text)
    assert ranked[0].destination.name == "Alpha"
