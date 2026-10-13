from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import replace
from datetime import datetime, timezone
from typing import Optional

from wanderlens.core.models import Destination

THIN_DESCRIPTION_CHARS = 40


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _load(conn: sqlite3.Connection, user_id: int, kind: str, ref_id, digest: str):
    row = conn.execute(
        "SELECT result FROM taste_enrichment "
        "WHERE user_id = ? AND kind = ? AND ref_id = ? AND input_hash = ?",
        (user_id, kind, str(ref_id), digest),
    ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["result"])
    except ValueError:
        return None


def _save(conn, user_id, kind, ref_id, digest, enricher, result) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO taste_enrichment "
        "(user_id, kind, ref_id, input_hash, model, prompt_version, result, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            user_id,
            kind,
            str(ref_id),
            digest,
            getattr(enricher, "model", ""),
            getattr(enricher, "prompt_version", ""),
            json.dumps(result),
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def enrich_trip_attributes(
    conn: sqlite3.Connection,
    user_id: int,
    trip_id: int,
    tags,
    enricher,
    context: str = "",
) -> list[str]:
    """Turn a trip's flat tags into structured canonical attributes, cached.

    Returns ``[]`` when no enricher is configured or the model errors, so the
    caller falls back to the deterministic tags.
    """
    if enricher is None:
        return []
    digest = _digest(
        {
            "tags": sorted(str(tag) for tag in tags),
            "context": context,
            "prompt": getattr(enricher, "prompt_version", ""),
        }
    )
    cached = _load(conn, user_id, "trip_attributes", trip_id, digest)
    if cached is not None:
        return cached
    try:
        result = [str(attribute).strip().lower() for attribute in enricher.attribute_trip(list(tags), context)]
    except Exception:
        return []
    result = [attribute for attribute in result if attribute]
    _save(conn, user_id, "trip_attributes", trip_id, digest, enricher, result)
    conn.commit()
    return result


def is_thin(destination: Destination) -> bool:
    return not destination.attributes and len(destination.description or "") < THIN_DESCRIPTION_CHARS


def enrich_destination(
    conn: sqlite3.Connection, user_id: int, destination: Destination, enricher
) -> Destination:
    """Return the Destination with a richer description when it is thin, cached.

    The original Destination is returned unchanged when no enricher is
    configured, the destination already has a rich representation, or the model
    errors.
    """
    if enricher is None or not is_thin(destination):
        return destination
    digest = _digest(
        {
            "name": destination.name,
            "country": destination.country,
            "attributes": list(destination.attributes),
            "description": destination.description,
            "prompt": getattr(enricher, "prompt_version", ""),
        }
    )
    cached = _load(conn, user_id, "destination", destination.id, digest)
    if cached is None:
        try:
            text = enricher.description(destination) or ""
        except Exception:
            text = ""
        cached = {"description": text.strip()}
        _save(conn, user_id, "destination", destination.id, digest, enricher, cached)
        conn.commit()
    text = cached.get("description") or ""
    if not text:
        return destination
    return replace(destination, description=text)
