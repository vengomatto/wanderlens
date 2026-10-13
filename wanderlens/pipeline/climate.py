from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from wanderlens.catalog.fetch import fetch_climate, fetch_trip_weather
from wanderlens.core.climate import band, best_months, climate_match, climate_profile
from wanderlens.core.models import Destination


def build_climate_profile(conn: sqlite3.Connection, user_id: int, session=None) -> dict:
    """Derive and store the user's climate preference from their trips."""
    rows = conn.execute(
        "SELECT id, start_at, end_at, lat, lon FROM trips "
        "WHERE user_id = ? AND lat IS NOT NULL AND lon IS NOT NULL AND start_at IS NOT NULL "
        "ORDER BY id",
        (user_id,),
    ).fetchall()
    per_trip: list[dict] = []
    for row in rows:
        cached = conn.execute(
            "SELECT temp_c, precip_mm, month FROM trip_weather WHERE user_id = ? AND trip_id = ?",
            (user_id, row["id"]),
        ).fetchone()
        if cached is not None:
            per_trip.append(
                {"temp_c": cached["temp_c"], "precip_mm": cached["precip_mm"], "month": cached["month"]}
            )
            continue
        try:
            weather = fetch_trip_weather(
                row["lat"],
                row["lon"],
                row["start_at"][:10],
                (row["end_at"] or row["start_at"])[:10],
                session=session,
            )
        except Exception:
            weather = None
        if not weather:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO trip_weather "
            "(user_id, trip_id, temp_c, precip_mm, month, fetched_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                row["id"],
                weather["temp_c"],
                weather["precip_mm"],
                weather["month"],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        per_trip.append(weather)
    conn.commit()

    profile = climate_profile(per_trip)
    if profile:
        _store_profile(conn, user_id, profile)
    return profile


def _store_profile(conn: sqlite3.Connection, user_id: int, profile: dict) -> None:
    conn.execute("DELETE FROM profile_entries WHERE user_id = ? AND factor = 'climate'", (user_id,))
    entries = [("temp_mean", profile["temp_mean"]), ("precip_mean", profile.get("precip_mean") or 0.0)]
    entries.extend((f"month:{month}", weight) for month, weight in (profile.get("months") or {}).items())
    for key, value in entries:
        conn.execute(
            "INSERT OR REPLACE INTO profile_entries (user_id, factor, key, value) "
            "VALUES (?, 'climate', ?, ?)",
            (user_id, key, value),
        )
    conn.commit()


def load_climate_profile(conn: sqlite3.Connection, user_id: int) -> dict:
    rows = conn.execute(
        "SELECT key, value FROM profile_entries WHERE user_id = ? AND factor = 'climate'",
        (user_id,),
    ).fetchall()
    if not rows:
        return {}
    profile: dict = {"months": {}}
    for row in rows:
        key = row["key"]
        if key == "temp_mean":
            profile["temp_mean"] = row["value"]
        elif key == "precip_mean":
            profile["precip_mean"] = row["value"]
        elif key.startswith("month:"):
            profile["months"][int(key.split(":", 1)[1])] = row["value"]
    if profile.get("temp_mean") is None:
        return {}
    profile["band"] = band(profile["temp_mean"])
    return profile


def ensure_destination_climate(
    conn: sqlite3.Connection, destination: Destination, profile: dict, session=None
) -> dict:
    row = conn.execute(
        "SELECT climate FROM destination_climate WHERE destination_id = ?", (destination.id,)
    ).fetchone()
    if row is not None and row["climate"]:
        try:
            monthly = json.loads(row["climate"])
        except ValueError:
            monthly = []
    else:
        try:
            monthly = fetch_climate(destination.lat, destination.lon, session=session)
        except Exception:
            monthly = []
        conn.execute(
            "INSERT OR REPLACE INTO destination_climate "
            "(destination_id, climate, best_months, match, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (
                destination.id,
                json.dumps(monthly),
                "[]",
                0.0,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()

    best = best_months(monthly, profile) if profile else []
    match = climate_match(monthly, profile) if profile else 0.0
    conn.execute(
        "UPDATE destination_climate SET best_months = ?, match = ? WHERE destination_id = ?",
        (json.dumps(best), match, destination.id),
    )
    conn.commit()
    return {"climate": monthly, "best_months": best, "match": match}


def load_destination_climate(conn: sqlite3.Connection, destination_id: str) -> dict:
    row = conn.execute(
        "SELECT climate, best_months, match FROM destination_climate WHERE destination_id = ?",
        (destination_id,),
    ).fetchone()
    if row is None:
        return {}
    try:
        monthly = json.loads(row["climate"] or "[]")
    except ValueError:
        monthly = []
    try:
        best = json.loads(row["best_months"] or "[]")
    except ValueError:
        best = []
    return {"climate": monthly, "best_months": best, "match": row["match"] or 0.0}
