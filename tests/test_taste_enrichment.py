from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db
from wanderlens.pipeline.enrichment import enrich_destination, enrich_trip_attributes


class StubEnricher:
    name = "stub"
    prompt_version = "v1"
    model = "stub-model"

    def __init__(self):
        self.trip_calls = 0
        self.desc_calls = 0
        self.received = None

    def attribute_trip(self, tags, context=""):
        self.trip_calls += 1
        self.received = list(tags)
        return ["coastal", "hiking"]

    def description(self, destination):
        self.desc_calls += 1
        return "a coastal town with hiking trails"


class BoomEnricher:
    model = "boom"
    prompt_version = "v1"

    def attribute_trip(self, tags, context=""):
        raise RuntimeError("model down")

    def description(self, destination):
        raise RuntimeError("model down")


def _conn(tmp_path):
    conn = connect(tmp_path / "e.sqlite3")
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.commit()
    return conn


def test_trip_attributes_are_cached(tmp_path):
    conn = _conn(tmp_path)
    enricher = StubEnricher()

    first = enrich_trip_attributes(conn, 1, 0, ["sea", "trail"], enricher)
    assert first == ["coastal", "hiking"]
    assert enricher.trip_calls == 1

    second = enrich_trip_attributes(conn, 1, 0, ["sea", "trail"], enricher)
    assert second == first
    assert enricher.trip_calls == 1, "cached result should not re-call the model"


def test_only_derived_text_reaches_the_enricher(tmp_path):
    conn = _conn(tmp_path)
    enricher = StubEnricher()

    enrich_trip_attributes(conn, 1, 0, ["sea", "trail"], enricher)

    assert enricher.received == ["sea", "trail"], "the seam gets tags, never photo paths"


def test_missing_enricher_falls_back(tmp_path):
    conn = _conn(tmp_path)
    assert enrich_trip_attributes(conn, 1, 0, ["sea"], None) == []


def test_enricher_error_falls_back(tmp_path):
    conn = _conn(tmp_path)
    assert enrich_trip_attributes(conn, 1, 0, ["sea"], BoomEnricher()) == []

    thin = Destination(id="d", name="D", lat=1, lon=1, country="X")
    assert enrich_destination(conn, 1, thin, BoomEnricher()) is thin


def test_destination_enrichment_is_cached_and_thin_only(tmp_path):
    conn = _conn(tmp_path)
    enricher = StubEnricher()

    thin = Destination(id="thin", name="Thin", lat=1, lon=1, country="X")
    enriched = enrich_destination(conn, 1, thin, enricher)
    assert "coastal" in enriched.description
    assert enricher.desc_calls == 1
    assert thin.description == "", "the original Destination is not mutated"

    enrich_destination(conn, 1, thin, enricher)
    assert enricher.desc_calls == 1, "cached destination enrichment is reused"

    rich = Destination(
        id="rich",
        name="Rich",
        lat=1,
        lon=1,
        country="X",
        attributes=["coastal"],
        description="a descriptive coastal town with many beaches",
    )
    assert enrich_destination(conn, 1, rich, enricher) is rich
    assert enricher.desc_calls == 1, "rich destinations are not enriched"
