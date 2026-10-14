from wanderlens.catalog.profiles import build_profile, keyless_profile, load_profile
from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db
from wanderlens.models.profiles import parse_profile


class StubWriter:
    model = "m"
    prompt_version = "v1"

    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def write(self, destination, facts):
        self.calls += 1
        return self.payload


def _conn(tmp_path):
    conn = connect(tmp_path / "p.sqlite3")
    init_db(conn)
    return conn


def _dest(**kwargs):
    return Destination(id="d", name="D", lat=1.0, lon=1.0, country="X", **kwargs)


def test_keyless_profile_from_attributes():
    profile = keyless_profile(_dest(attributes=["coastal", "beach"]))
    assert profile["vibe"].get("coastal", 0) > 0
    assert profile["vibe"].get("beach", 0) > 0
    assert profile["source"] == "keyless"
    assert profile["estimated"] == []


def test_build_profile_merges_and_marks_estimated(tmp_path):
    conn = _conn(tmp_path)
    writer = StubWriter(
        {"vibe": {"coastal": 0.9}, "typical_stay_days": 5, "family_suitability": "high", "summary": "Nice."}
    )

    profile = build_profile(conn, _dest(attributes=["coastal"]), writer=writer)

    assert profile["vibe"]["coastal"] == 0.9
    assert profile["typical_stay_days"] == 5
    assert "typical_stay_days" in profile["estimated"]
    assert "summary" in profile["estimated"]
    assert profile["source"] == "llm"

    build_profile(conn, _dest(attributes=["coastal"]), writer=writer)
    assert writer.calls == 1, "cached profile should not re-call the model"
    assert load_profile(conn, "d")["typical_stay_days"] == 5


def test_parse_profile_validates_output():
    assert parse_profile("not json") == {}
    assert parse_profile('{"vibe": {"x": 2}, "typical_stay_days": -1}') == {}
    cleaned = parse_profile('{"vibe": {"coastal": 0.9}, "walkability": "high", "junk": 1}')
    assert cleaned == {"vibe": {"coastal": 0.9}, "walkability": "high"}


def test_build_profile_writer_error_falls_back(tmp_path):
    conn = _conn(tmp_path)

    class Boom:
        model = "m"
        prompt_version = "v"

        def write(self, *a):
            raise RuntimeError("no")

    assert build_profile(conn, _dest(attributes=["coastal"]), writer=Boom())["source"] == "keyless"
