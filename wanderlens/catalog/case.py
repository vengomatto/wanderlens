from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from wanderlens.catalog.fetch import fetch_wikivoyage_page
from wanderlens.core.models import Destination

_MAX_NARRATIVE = 700


def _digest(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _load(conn: sqlite3.Connection, destination_id: str, digest: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT narrative, sources, source FROM destination_case "
        "WHERE destination_id = ? AND input_hash = ?",
        (destination_id, digest),
    ).fetchone()
    if row is None:
        return None
    try:
        sources = json.loads(row["sources"] or "[]")
    except ValueError:
        sources = []
    return {"narrative": row["narrative"] or "", "sources": sources, "source": row["source"] or ""}


def _store(conn, destination_id, digest, model, prompt_version, case) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO destination_case "
        "(destination_id, input_hash, model, prompt_version, narrative, sources, source, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            destination_id,
            digest,
            model,
            prompt_version,
            case.get("narrative", ""),
            json.dumps(case.get("sources", [])),
            case.get("source", ""),
            datetime.now(timezone.utc).isoformat(),
        ),
    )


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]


def _keyless_case(destination: Destination, facts: dict) -> dict:
    text = facts.get("extract") or destination.description or ""
    narrative = " ".join(_sentences(text)[:3])[:_MAX_NARRATIVE]
    if not narrative:
        narrative = (
            f"{destination.name}, {destination.country} — a place to explore"
            if destination.country
            else destination.name
        )
    name = destination.name.replace(" ", "_")
    sources = []
    if facts.get("page_url"):
        sources.append({"title": f"Wikivoyage: {destination.name}", "url": facts["page_url"]})
    sources.append({"title": f"Wikipedia: {destination.name}", "url": f"https://en.wikipedia.org/wiki/{name}"})
    if facts.get("wikidata_id"):
        sources.append(
            {"title": "Wikidata", "url": f"https://www.wikidata.org/wiki/{facts['wikidata_id']}"}
        )
    sources.append(
        {
            "title": f"Commons: {destination.name}",
            "url": f"https://commons.wikimedia.org/wiki/Category:{name}",
        }
    )
    return {"narrative": narrative, "sources": sources, "source": "keyless"}


def _merge_sources(primary: list[dict], fallback: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for item in [*(primary or []), *(fallback or [])]:
        url = (item.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({"title": item.get("title", ""), "url": url})
    return out


def gather_facts(destination: Destination, session=None) -> dict:
    try:
        voyage = fetch_wikivoyage_page(destination.name, destination.country, session=session) or {}
    except Exception:
        voyage = {}
    return {
        "extract": voyage.get("extract", ""),
        "page_url": voyage.get("page_url", ""),
        "wikidata_id": voyage.get("wikidata_id", ""),
    }


def build_case(
    conn: sqlite3.Connection,
    destination: Destination,
    session=None,
    searcher=None,
    writer=None,
    refresh: bool = False,
) -> dict:
    """Build and cache a sourced case for a Destination. Never raises."""
    model = getattr(writer, "model", "") if writer is not None else ""
    prompt = getattr(writer, "prompt_version", "") if writer is not None else ""
    digest = _digest(
        {
            "id": destination.id,
            "name": destination.name,
            "country": destination.country,
            "model": model,
            "prompt": prompt,
        }
    )
    if not refresh:
        cached = _load(conn, destination.id, digest)
        if cached is not None:
            return cached

    facts = gather_facts(destination, session)
    search_results: list[dict] = []
    if searcher is not None:
        try:
            search_results = searcher.search(
                f"{destination.name} {destination.country} travel", limit=5
            ) or []
        except Exception:
            search_results = []

    case = _keyless_case(destination, facts)
    if writer is not None and (facts.get("extract") or search_results):
        try:
            written = writer.write(destination, facts, search_results) or {}
        except Exception:
            written = {}
        if written.get("narrative"):
            case = {
                "narrative": written["narrative"],
                "sources": _merge_sources(written.get("sources", []), case["sources"]),
                "source": "llm",
            }

    _store(conn, destination.id, digest, model, prompt, case)
    conn.commit()
    return case


def load_case(conn: sqlite3.Connection, destination_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT narrative, sources, source FROM destination_case "
        "WHERE destination_id = ? ORDER BY fetched_at DESC LIMIT 1",
        (destination_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        sources = json.loads(row["sources"] or "[]")
    except ValueError:
        sources = []
    return {"narrative": row["narrative"] or "", "sources": sources, "source": row["source"] or ""}
