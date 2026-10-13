from wanderlens.catalog import case as case_mod
from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db


class StubWriter:
    name = "stub"
    prompt_version = "v1"
    model = "stub-model"

    def __init__(self):
        self.calls = 0

    def write(self, destination, facts, search_results):
        self.calls += 1
        return {
            "narrative": "Visit for the bay and the walled old town.",
            "sources": [{"title": "Guide", "url": "https://example.com/kotor"}],
        }


class StubSearcher:
    name = "stub"

    def search(self, query, limit=5):
        return [{"title": "Result", "url": "https://example.com/kotor", "snippet": "x"}]


def _conn(tmp_path):
    conn = connect(tmp_path / "c.sqlite3")
    init_db(conn)
    return conn


def _destination():
    return Destination(id="kotor", name="Kotor", lat=42.4, lon=18.7, country="Montenegro")


def test_keyless_case(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(
        case_mod,
        "gather_facts",
        lambda d, session=None: {
            "extract": "Kotor is a coastal town. It has a walled old town. The bay is stunning.",
            "page_url": "https://en.wikivoyage.org/wiki/Kotor",
            "wikidata_id": "Q123",
        },
    )

    case = case_mod.build_case(conn, _destination())

    assert case["source"] == "keyless"
    assert "coastal town" in case["narrative"]
    assert any(s["url"].startswith("https://en.wikivoyage.org") for s in case["sources"])


def test_case_is_cached(tmp_path, monkeypatch):
    calls = {"n": 0}

    def facts(d, session=None):
        calls["n"] += 1
        return {"extract": "A town.", "page_url": "", "wikidata_id": ""}

    monkeypatch.setattr(case_mod, "gather_facts", facts)
    conn = _conn(tmp_path)
    destination = _destination()

    case_mod.build_case(conn, destination)
    case_mod.build_case(conn, destination)

    assert calls["n"] == 1, "the case should be cached"


def test_case_uses_writer_and_searcher(tmp_path, monkeypatch):
    monkeypatch.setattr(
        case_mod, "gather_facts", lambda d, session=None: {"extract": "A town.", "page_url": "", "wikidata_id": ""}
    )
    conn = _conn(tmp_path)
    writer = StubWriter()

    case = case_mod.build_case(conn, _destination(), searcher=StubSearcher(), writer=writer)

    assert case["source"] == "llm"
    assert "bay" in case["narrative"]
    assert any(s["url"] == "https://example.com/kotor" for s in case["sources"])


def test_case_writer_error_falls_back(tmp_path, monkeypatch):
    monkeypatch.setattr(
        case_mod, "gather_facts", lambda d, session=None: {"extract": "A town.", "page_url": "", "wikidata_id": ""}
    )

    class Boom:
        model = "boom"
        prompt_version = "v1"

        def write(self, *args):
            raise RuntimeError("model down")

    conn = _conn(tmp_path)
    case = case_mod.build_case(conn, _destination(), writer=Boom())

    assert case["source"] == "keyless"
    assert case["narrative"]
