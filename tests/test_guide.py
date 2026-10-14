from wanderlens.catalog.fetch import (
    OPENLIBRARY_SEARCH,
    OPEN_METEO_ARCHIVE,
    WIKIDATA_API,
    WIKIDATA_ENDPOINT,
    WIKIVOYAGE_API,
    fetch_climate,
    fetch_openlibrary_books,
    fetch_wikidata_claim,
    fetch_wikidata_narrative_works,
    fetch_wikivoyage_page,
    fetch_wikivoyage_wikitext,
    parse_pois,
)
from wanderlens.catalog.guide import build_guides_for, fetch_guide, gather_guide, is_guide_cached
from wanderlens.config import Config
from wanderlens.core.models import Destination
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
    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, **kwargs):
        params = kwargs.get("params") or {}
        self.calls.append((url, params.get("action")))
        for (needle, action), response in self.routes.items():
            if needle in url and (action is None or action == params.get("action")):
                return response() if callable(response) else response
        return FakeResponse(status=404)


WV_PAGE = {
    "query": {
        "pages": {
            "1": {
                "title": "Algarve",
                "fullurl": "https://en.wikivoyage.org/wiki/Algarve",
                "extract": "The Algarve is Portugal's southern coast.",
                "pageprops": {"wikibase_item": "Q1234"},
                "extlinks": [{"*": "https://www.visitalgarve.pt"}],
                "links": [{"title": "Algarve coast itinerary", "ns": 0}],
            }
        }
    }
}
WV_WIKITEXT = {
    "parse": {
        "wikitext": {
            "*": "{{see | name=Benagil Cave | lat=37.08 | long=-8.42 }}\n"
            "{{do | name=Surfing | lat=37.0 | long=-8.5 }}\n"
            "{{see | name=Broken | lat= | long= }}"
        }
    }
}
WIKIDATA_CLAIMS = {
    "entities": {
        "Q1234": {"claims": {"P856": [{"mainsnak": {"datavalue": {"value": "https://www.visitalgarve.pt"}}}]}}
    }
}
SPARQL_WORKS = {
    "results": {
        "bindings": [
            {
                "workLabel": {"value": "The Last Train to Lisbon"},
                "work": {"value": "http://www.wikidata.org/entity/Q1"},
            }
        ]
    }
}
OPENLIBRARY = {
    "docs": [{"title": "Algarve Blues", "author_name": ["A. Author"], "key": "/works/OL1W"}]
}
CLIMATE = {
    "daily": {
        "time": [f"2020-{m:02d}-15" for m in range(1, 13)],
        "temperature_2m_mean": [10, 11, 14, 17, 20, 24, 27, 27, 24, 19, 14, 11],
        "precipitation_sum": [80, 70, 60, 50, 30, 10, 5, 5, 20, 60, 90, 100],
    }
}


def _session():
    return FakeSession(
        {
            (WIKIVOYAGE_API, "query"): FakeResponse(WV_PAGE),
            (WIKIVOYAGE_API, "parse"): FakeResponse(WV_WIKITEXT),
            (WIKIDATA_ENDPOINT, None): FakeResponse(SPARQL_WORKS),
            (WIKIDATA_API, "wbgetentities"): FakeResponse(WIKIDATA_CLAIMS),
            (OPENLIBRARY_SEARCH, None): FakeResponse(OPENLIBRARY),
            (OPEN_METEO_ARCHIVE, None): FakeResponse(CLIMATE),
        }
    )


def _destination():
    return Destination(id="wv:Algarve", name="Algarve", lat=37.0, lon=-8.0, country="Portugal")


def test_parse_pois_extracts_see_and_do_with_coordinates():
    pois = parse_pois(WV_WIKITEXT["parse"]["wikitext"]["*"])

    assert [p["name"] for p in pois] == ["Benagil Cave", "Surfing"]
    assert pois[0]["kind"] == "see"
    assert pois[0]["lat"] == 37.08
    assert pois[1]["kind"] == "do"


def test_parse_pois_handles_listing_and_marker_templates():
    wikitext = (
        "{{listing | type=see | name=Lighthouse | lat=1.0 | long=2.0 }}"
        "{{marker | type=do | name=Diving | lat=3.0 | long=4.0 }}"
    )
    pois = parse_pois(wikitext)
    assert [p["name"] for p in pois] == ["Lighthouse", "Diving"]
    assert pois[0]["kind"] == "see"
    assert pois[1]["kind"] == "do"


def test_gather_guide_caps_understand():
    long_extract = "sentence text. " * 1000
    page = {
        "query": {
            "pages": {
                "1": {
                    "title": "X",
                    "fullurl": "",
                    "extract": long_extract,
                    "pageprops": {},
                    "extlinks": [],
                    "links": [],
                }
            }
        }
    }
    session = FakeSession({(WIKIVOYAGE_API, "query"): FakeResponse(page)})
    guide = gather_guide(_destination(), session=session)
    assert len(guide["understand"]) <= 2501
    assert guide["understand"].endswith("…")


def test_fetch_wikivoyage_page_and_wikitext():
    session = _session()
    page = fetch_wikivoyage_page("Algarve", "Portugal", session=session)
    wikitext = fetch_wikivoyage_wikitext("Algarve", session=session)

    assert page["extract"].startswith("The Algarve")
    assert page["wikidata_id"] == "Q1234"
    assert page["external_links"] == ["https://www.visitalgarve.pt"]
    assert page["itineraries"][0]["title"] == "Algarve coast itinerary"
    assert "Benagil Cave" in wikitext


def test_fetch_openlibrary_books():
    books = fetch_openlibrary_books("Algarve", session=_session())
    assert books[0]["title"] == "Algarve Blues"
    assert books[0]["author"] == "A. Author"


def test_fetch_wikidata_books_and_films_and_site():
    session = _session()
    assert fetch_wikidata_claim("Q1234", "P856", session=session) == "https://www.visitalgarve.pt"
    works = fetch_wikidata_narrative_works("Q1234", ("Q8261",), session=session)
    assert works[0]["title"] == "The Last Train to Lisbon"


def test_fetch_climate_monthly_summary():
    climate = fetch_climate(37.0, -8.0, session=_session())
    assert len(climate) == 12
    assert climate[0]["month"] == 1
    assert climate[0]["temp_c"] == 10.0
    assert climate[6]["temp_c"] == 27.0


def test_gather_guide_sections():
    guide = gather_guide(_destination(), session=_session())

    assert guide["understand"].startswith("The Algarve")
    labels = {link["label"] for link in guide["links"]}
    assert "Wikivoyage" in labels
    assert "Official site" in labels
    assert guide["books"][0]["title"] in {"Algarve Blues", "The Last Train to Lisbon"}
    assert len(guide["pois"]) == 2
    assert len(guide["climate"]) == 12
    assert guide["films"]
    assert guide["itineraries"][0]["source"] == "wikivoyage"


def test_gather_guide_partial_without_network():
    guide = gather_guide(_destination(), session=FakeSession({}))
    assert guide["understand"] == ""
    assert guide["pois"] == []
    assert guide["books"] == []


def test_fetch_guide_is_cached(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    session = _session()

    assert fetch_guide(conn, _destination(), session=session) is True
    calls = len(session.calls)
    assert is_guide_cached(conn, "wv:Algarve")

    assert fetch_guide(conn, _destination(), session=session) is False
    assert len(session.calls) == calls
    assert fetch_guide(conn, _destination(), session=session, refresh=True) is True


class FakeSynthesizer:
    name = "llm"
    prompt_version = "itinerary-v1"
    model = "test-model"

    def synthesize(self, destination, pois, days, search_results=None):
        return [{"title": "Day 1", "summary": "Arrive", "items": ["Beach"]}]


class BoomSynthesizer:
    name = "llm"
    prompt_version = "itinerary-v1"
    model = "test-model"

    def synthesize(self, destination, pois, days, search_results=None):
        raise RuntimeError("no")


def test_llm_itinerary_included_and_labelled():
    guide = gather_guide(_destination(), session=_session(), synthesizer=FakeSynthesizer())
    llm = [it for it in guide["itineraries"] if it["source"] == "llm"]
    assert llm and llm[0]["days"][0]["title"] == "Day 1"
    assert llm[0]["prompt_version"] == "itinerary-v1"


def test_llm_itinerary_failure_falls_back_to_curated():
    guide = gather_guide(_destination(), session=_session(), synthesizer=BoomSynthesizer())
    assert all(it["source"] != "llm" for it in guide["itineraries"])
    assert guide["itineraries"][0]["source"] == "wikivoyage"


def test_build_guides_for(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)
    destinations = [_destination(), Destination(id="wv:Kotor", name="Kotor", lat=42.4, lon=18.7, country="Montenegro")]

    built = build_guides_for(conn, destinations, session=_session())
    assert built == 2
    assert conn.execute("SELECT COUNT(*) FROM destination_guide").fetchone()[0] == 2


def test_run_guide_builds_for_recommendations(tmp_path):
    from wanderlens.pipeline.guide import run_guide

    config = Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=tmp_path / "catalog",
        vlm_provider="t",
        vlm_model="t",
        api_key=None,
    )
    conn = connect(config.db_path)
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.execute(
        "INSERT INTO recommendations "
        "(user_id, run_id, rank, destination_id, score, destination_name, "
        " destination_country, destination_lat, destination_lon) "
        "VALUES (1, 1, 1, 'wv:Algarve', 0.8, 'Algarve', 'Portugal', 37.0, -8.0)"
    )
    conn.commit()

    assert run_guide(config, session=_session()) == 1
    assert is_guide_cached(conn, "wv:Algarve")
    assert run_guide(config, session=_session()) == 0  # cached


def test_derived_itinerary_without_model():
    guide = gather_guide(_destination(), session=_session())

    derived = [it for it in guide["itineraries"] if it["source"] == "derived"]
    assert derived and derived[0]["days"]
    assert any("Benagil Cave" in day["items"] for day in derived[0]["days"])


def test_itinerary_groups_by_proximity():
    from wanderlens.catalog.guide import _poi_itinerary

    pois = [
        {"name": "A1", "lat": 10.0, "lon": 10.0},
        {"name": "A2", "lat": 10.01, "lon": 10.01},
        {"name": "B1", "lat": 20.0, "lon": 20.0},
        {"name": "B2", "lat": 20.01, "lon": 20.01},
    ]

    groups = [set(day["items"]) for day in _poi_itinerary(pois, 2)]

    assert {"A1", "A2"} in groups
    assert {"B1", "B2"} in groups


def test_itinerary_falls_back_without_coordinates():
    from wanderlens.catalog.guide import _poi_itinerary

    plan = _poi_itinerary([{"name": n} for n in "ABCD"], 2)

    assert [len(day["items"]) for day in plan] == [2, 2]


def test_diaries_gathered_and_deduped():
    guide = gather_guide(
        _destination(),
        session=_session(),
        blogs=["https://www.visitalgarve.pt", "https://example.org/blog"],
    )

    urls = [diary["url"] for diary in guide["diaries"]]
    assert "https://www.visitalgarve.pt" in urls
    assert "https://example.org/blog" in urls
    assert len(urls) == len(set(urls)), "diaries are deduplicated"


def test_itinerary_is_grounded_in_search():
    class Searcher:
        name = "stub"

        def __init__(self):
            self.queries = []

        def search(self, query, limit=5):
            self.queries.append(query)
            return [{"title": "Algarve in 3 days", "url": "u", "snippet": "s"}]

    class RecordingSynth:
        prompt_version = "v"
        model = "m"

        def __init__(self):
            self.seen = None

        def synthesize(self, destination, pois, days, search_results=None):
            self.seen = search_results
            return [{"title": "Day 1", "summary": "", "items": []}]

    searcher = Searcher()
    synth = RecordingSynth()

    guide = gather_guide(
        _destination(), session=_session(), synthesizer=synth, searcher=searcher
    )

    assert searcher.queries
    assert synth.seen and synth.seen[0]["title"] == "Algarve in 3 days"
    assert any(it["source"] == "llm" for it in guide["itineraries"])

