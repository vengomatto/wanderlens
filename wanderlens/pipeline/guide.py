from __future__ import annotations

import sqlite3
from typing import Optional

from wanderlens.catalog.guide import build_guides_for
from wanderlens.config import Config
from wanderlens.core.models import Destination
from wanderlens.db import connect, init_db


def load_recommended_destinations(
    conn: sqlite3.Connection, user_id: int, count: Optional[int] = None
) -> list[Destination]:
    rows = conn.execute(
        "SELECT destination_id, destination_name, destination_country, destination_lat, "
        "destination_lon, destination_description FROM recommendations "
        "WHERE user_id = ? AND run_id = "
        "(SELECT COALESCE(MAX(run_id), 0) FROM recommendations WHERE user_id = ?) "
        "ORDER BY rank",
        (user_id, user_id),
    ).fetchall()
    destinations = [
        Destination(
            id=row["destination_id"],
            name=row["destination_name"] or row["destination_id"],
            lat=row["destination_lat"],
            lon=row["destination_lon"],
            country=row["destination_country"] or "",
            description=row["destination_description"] or "",
        )
        for row in rows
    ]
    return destinations[:count] if count else destinations


def run_guide(
    config: Config,
    user_name: str = "owner",
    count: Optional[int] = None,
    refresh: bool = False,
    synthesizer=None,
    session=None,
    searcher=None,
) -> int:
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)
    destinations = load_recommended_destinations(conn, user_id, count)
    return build_guides_for(
        conn,
        destinations,
        session=session,
        synthesizer=synthesizer,
        refresh=refresh,
        blogs=getattr(config, "travel_blogs", []),
        searcher=searcher,
    )
