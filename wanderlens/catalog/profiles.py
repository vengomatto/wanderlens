from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from wanderlens.core.models import Destination
from wanderlens.core.vocabulary import canonicalize

ESTIMATED_KEYS = ("typical_stay_days", "family_suitability", "walkability", "base_camp", "summary")


def keyless_profile(destination: Destination) -> dict:
    """A deterministic baseline profile from the Destination's own attributes."""
    vibe: dict[str, float] = {}
    for tag in destination.attributes:
        for attribute in canonicalize(tag):
            vibe[attribute] = vibe.get(attribute, 0.0) + 0.6
    vibe = {attribute: min(1.0, round(value, 3)) for attribute, value in vibe.items()}
    return {"vibe": vibe, "estimated": [], "source": "keyless"}


def facts_for(destination: Destination) -> dict:
    return {
        "description": destination.description,
        "granularity": destination.granularity,
        "attributes": list(destination.attributes),
    }


def _digest(destination: Destination, model: str, prompt: str) -> str:
    payload = {
        "id": destination.id,
        "name": destination.name,
        "country": destination.country,
        "description": destination.description,
        "attributes": list(destination.attributes),
        "model": model,
        "prompt": prompt,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _load(conn: sqlite3.Connection, destination_id: str, digest: str):
    row = conn.execute(
        "SELECT payload FROM destination_profiles WHERE destination_id = ? AND input_hash = ?",
        (destination_id, digest),
    ).fetchone()
    if row is None:
        return None
    try:
        return json.loads(row["payload"])
    except ValueError:
        return None


def build_profile(
    conn: sqlite3.Connection,
    destination: Destination,
    writer=None,
    refresh: bool = False,
) -> dict:
    """Build and cache a Destination's profile; never fatal."""
    model = getattr(writer, "model", "") if writer is not None else ""
    prompt = getattr(writer, "prompt_version", "") if writer is not None else ""
    digest = _digest(destination, model, prompt)
    if not refresh:
        cached = _load(conn, destination.id, digest)
        if cached is not None:
            return cached

    profile = keyless_profile(destination)
    if writer is not None:
        try:
            written = writer.write(destination, facts_for(destination)) or {}
        except Exception:
            written = {}
        if written:
            if written.get("vibe"):
                profile["vibe"] = written["vibe"]
            for key in ESTIMATED_KEYS:
                if key in written:
                    profile[key] = written[key]
                    profile["estimated"].append(key)
            profile["source"] = "llm"

    conn.execute(
        "INSERT OR REPLACE INTO destination_profiles "
        "(destination_id, input_hash, model, prompt_version, payload, source, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            destination.id,
            digest,
            model,
            prompt,
            json.dumps(profile),
            profile["source"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    return profile


def load_profile(conn: sqlite3.Connection, destination_id: str) -> dict:
    row = conn.execute(
        "SELECT payload FROM destination_profiles WHERE destination_id = ? "
        "ORDER BY fetched_at DESC LIMIT 1",
        (destination_id,),
    ).fetchone()
    if row is None:
        return {}
    try:
        return json.loads(row["payload"])
    except ValueError:
        return {}
