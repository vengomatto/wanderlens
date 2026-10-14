from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db
from wanderlens.pipeline.brief import filter_by_travel, load_brief, save_brief


def _conn(tmp_path):
    conn = connect(tmp_path / "b.sqlite3")
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.commit()
    return conn


def test_save_and_load_brief_keeps_other_fields(tmp_path):
    conn = _conn(tmp_path)

    save_brief(conn, 1, adults=2, children=1, pace="relaxed")
    brief = load_brief(conn, 1)
    assert brief["adults"] == 2
    assert brief["children"] == 1
    assert brief["pace"] == "relaxed"

    save_brief(conn, 1, season="summer")
    brief = load_brief(conn, 1)
    assert brief["adults"] == 2, "partial update should keep other fields"
    assert brief["season"] == "summer"


def test_empty_brief(tmp_path):
    assert load_brief(_conn(tmp_path), 1) == {}


def test_filter_by_travel():
    far = Destination(id="far", name="Far", lat=60.0, lon=10.0, country="X")
    near = Destination(id="near", name="Near", lat=44.1, lon=9.6, country="Y")

    kept = [d.id for d in filter_by_travel([far, near], {"home_lat": 44.1, "home_lon": 9.6, "max_travel_km": 500})]
    assert kept == ["near"]

    assert [d.id for d in filter_by_travel([far, near], {})] == ["far", "near"]
