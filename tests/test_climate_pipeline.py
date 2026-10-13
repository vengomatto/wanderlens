from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db
from wanderlens.pipeline.climate import (
    build_climate_profile,
    ensure_destination_climate,
    load_climate_profile,
    load_destination_climate,
)

DAILY = {
    "daily": {
        "time": ["2024-07-01", "2024-07-02", "2024-07-03"],
        "temperature_2m_mean": [22.0, 24.0, 20.0],
        "precipitation_sum": [0.0, 2.0, 0.0],
    }
}


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def get(self, url, **kwargs):
        self.calls += 1
        return _Response(self.payload)


def _conn(tmp_path):
    conn = connect(tmp_path / "c.sqlite3")
    init_db(conn)
    conn.execute("INSERT INTO users (id, name) VALUES (1, 'owner')")
    conn.execute(
        "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
        "VALUES (1, 0, '2024-07-01T00:00:00', '2024-07-03T00:00:00', 'X', 'Y', 42.0, 18.0)"
    )
    conn.commit()
    return conn


def test_climate_profile_is_built_and_cached(tmp_path):
    conn = _conn(tmp_path)
    session = FakeSession(DAILY)

    profile = build_climate_profile(conn, 1, session=session)

    assert profile["temp_mean"] == 22.0
    assert profile["band"] == "warm"
    assert session.calls == 1

    build_climate_profile(conn, 1, session=session)
    assert session.calls == 1, "trip weather should be cached"

    assert load_climate_profile(conn, 1)["temp_mean"] == 22.0


def test_climate_profile_tolerates_missing_data(tmp_path):
    conn = _conn(tmp_path)
    session = FakeSession({"daily": {"time": [], "temperature_2m_mean": [], "precipitation_sum": []}})

    assert build_climate_profile(conn, 1, session=session) == {}


def test_destination_climate_match_and_best_months(tmp_path):
    conn = _conn(tmp_path)
    destination = Destination(id="d", name="D", lat=42.0, lon=18.0, country="X")
    profile = {"temp_mean": 22.0, "precip_mean": 1.0, "months": {7: 1.0}}
    session = FakeSession(DAILY)

    data = ensure_destination_climate(conn, destination, profile, session=session)

    assert data["match"] > 0
    assert 7 in data["best_months"]
    assert session.calls == 1

    stored = load_destination_climate(conn, "d")
    assert stored["match"] == data["match"]
    assert stored["best_months"] == data["best_months"]
