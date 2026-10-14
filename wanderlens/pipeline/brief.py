from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from wanderlens.core.models import Destination
from wanderlens.core.taste import haversine_km

FIELDS = (
    "adults",
    "children",
    "pace",
    "season",
    "max_travel_km",
    "home_lat",
    "home_lon",
    "budget",
)


def load_brief(conn: sqlite3.Connection, user_id: int) -> dict:
    row = conn.execute(
        "SELECT * FROM traveller_brief WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return {}
    return {field: row[field] for field in FIELDS if row[field] is not None}


def save_brief(conn: sqlite3.Connection, user_id: int, **fields) -> dict:
    """Upsert the given fields, keeping the rest; None values are ignored."""
    current = load_brief(conn, user_id)
    data = {field: fields.get(field, current.get(field)) for field in FIELDS}
    conn.execute(
        "INSERT OR REPLACE INTO traveller_brief "
        "(user_id, adults, children, pace, season, max_travel_km, home_lat, home_lon, budget, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            data["adults"],
            data["children"],
            data["pace"],
            data["season"],
            data["max_travel_km"],
            data["home_lat"],
            data["home_lon"],
            data["budget"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return load_brief(conn, user_id)


def filter_by_travel(destinations, brief: dict) -> list[Destination]:
    """Keep Destinations within the brief's maximum distance from home."""
    km = brief.get("max_travel_km")
    lat = brief.get("home_lat")
    lon = brief.get("home_lon")
    if not km or lat is None or lon is None:
        return list(destinations)
    return [d for d in destinations if haversine_km(d.lat, d.lon, lat, lon) <= km]
