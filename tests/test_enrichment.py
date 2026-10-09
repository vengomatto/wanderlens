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
)
COUNTRIES = "IT\tITA\t380\tIT\tItaly\tRome\t60360000\tEurope\tItaly\tEUR\tEuro\t+39\t.it\tIT\t^\n"


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


def test_enrich_records_sets_description_and_tolerates_failure():
    records = [{"name": "A", "description": ""}, {"name": "B", "description": ""}]

    def flaky(record):
        if record["name"] == "B":
            raise RuntimeError("network")
        return "coastal town"

    enrich_records(records, fetch=flaky)

    assert records[0]["description"] == "coastal town"
    assert records[1]["description"] == ""


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
    calls = []

    def stub(record):
        calls.append(record["name"])
        return f"coastal town near {record['name']}"

    first = default_catalog(config, description_fetcher=stub)
    assert {d.name for d in first.candidates()} == {"Genoa", "Rome"}
    assert all(d.description for d in first.candidates())
    assert len(calls) == 2

    second = default_catalog(config, description_fetcher=stub)
    assert len(calls) == 2, "cache should prevent refetching"
    assert {d.name for d in second.candidates()} == {"Genoa", "Rome"}


def test_described_destination_ranks_above_undescribed():
    def embed_text(text):
        return np.array([1.0, 0.0] if "coast" in text.lower() else [0.0, 1.0], dtype=np.float32)

    taste = np.array([1.0, 0.0], dtype=np.float32)
    described = Destination(id="a", name="Alpha", lat=1, lon=1, country="Greece", description="a coastal town")
    plain = Destination(id="b", name="Beta", lat=1, lon=1, country="Greece", description="")

    ranked = rank_destinations(taste, [plain, described], embed_text)
    assert ranked[0].destination.name == "Alpha"
