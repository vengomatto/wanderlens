from __future__ import annotations

import datetime as dt
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from wanderlens.catalog.fetch import USER_AGENT
from wanderlens.core.recommend import normalize_popularity

WIKIMEDIA_PAGEVIEWS = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/user/{article}/monthly/{start}/{end}"
)


def fetch_pageviews(title: str, session=None, timeout: int = 30, months: int = 12) -> Optional[int]:
    """Total Wikipedia pageviews over the recent months, or ``None`` if unknown."""
    import requests

    if not title:
        return None
    end = dt.date.today().replace(day=1)
    start = (end - dt.timedelta(days=31 * months)).replace(day=1)
    url = WIKIMEDIA_PAGEVIEWS.format(
        article=title.replace(" ", "_"),
        start=start.strftime("%Y%m%d"),
        end=end.strftime("%Y%m%d"),
    )
    response = (session or requests).get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    items = response.json().get("items", [])
    if not items:
        return None
    return sum(int(item.get("views", 0)) for item in items)


def is_cached(conn: sqlite3.Connection, destination_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM destination_popularity WHERE destination_id = ?", (destination_id,)
    ).fetchone()
    return row is not None


def fetch_popularity_for(conn: sqlite3.Connection, destinations, session=None) -> dict[str, float]:
    """Fetch and cache popularity for a batch; returns {destination_id: score}."""
    scores: dict[str, float] = {}
    for destination in destinations:
        if is_cached(conn, destination.id):
            row = conn.execute(
                "SELECT score FROM destination_popularity WHERE destination_id = ?",
                (destination.id,),
            ).fetchone()
            if row is not None and row["score"] is not None:
                scores[destination.id] = row["score"]
            continue
        try:
            total = fetch_pageviews(destination.name, session=session)
        except Exception:
            total = None
        score = normalize_popularity(total)
        conn.execute(
            "INSERT OR REPLACE INTO destination_popularity "
            "(destination_id, pageviews, score, fetched_at) VALUES (?, ?, ?, ?)",
            (destination.id, total, score, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        if score is not None:
            scores[destination.id] = score
    return scores
