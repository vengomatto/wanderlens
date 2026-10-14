from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from wanderlens.catalog.fetch import (
    BOOK_TYPES,
    FILM_TYPES,
    fetch_climate,
    fetch_openlibrary_books,
    fetch_wikidata_claim,
    fetch_wikidata_narrative_works,
    fetch_wikivoyage_page,
    fetch_wikivoyage_wikitext,
    parse_pois,
)
from wanderlens.core.models import Destination

DEFAULT_ITINERARY_DAYS = 4
MAX_LINKS = 10
MAX_UNDERSTAND = 2500
MAX_DIARIES = 12


def _truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return cut + "…"


def is_guide_cached(conn: sqlite3.Connection, destination_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM destination_guide WHERE destination_id = ?", (destination_id,)
    ).fetchone()
    return row is not None


def gather_guide(
    destination: Destination,
    session=None,
    synthesizer=None,
    days: int = DEFAULT_ITINERARY_DAYS,
    blogs=None,
    searcher=None,
) -> dict:
    """Gather every guide section best-effort; a missing source omits its section."""
    try:
        voyage = fetch_wikivoyage_page(destination.name, destination.country, session=session)
    except Exception:
        voyage = None
    wikidata_id = (voyage or {}).get("wikidata_id", "")

    pois: list[dict] = []
    if voyage and voyage.get("title"):
        try:
            wikitext = fetch_wikivoyage_wikitext(voyage["title"], session=session)
            pois = parse_pois(wikitext)
        except Exception:
            pois = []

    search_results: list[dict] = []
    if searcher is not None and synthesizer is not None:
        try:
            search_results = searcher.search(
                f"{destination.name} {destination.country} itinerary", limit=5
            ) or []
        except Exception:
            search_results = []

    return {
        "understand": _truncate((voyage or {}).get("extract", ""), MAX_UNDERSTAND),
        "links": _links(destination, voyage, wikidata_id, session),
        "books": _books(destination, wikidata_id, session),
        "pois": pois,
        "climate": _climate(destination, session),
        "films": _films(wikidata_id, session),
        "itineraries": _itineraries(destination, voyage, pois, synthesizer, days, search_results),
        "diaries": _diaries(destination, voyage, blogs),
    }


def _dedupe(items: list[dict], key: str = "url") -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        value = str(item.get(key, "")).strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(item)
    return out


def _domain_label(url: str) -> str:
    host = urlparse(url).netloc or url
    return host[4:] if host.startswith("www.") else host


def _links(destination: Destination, voyage, wikidata_id: str, session) -> list[dict]:
    links: list[dict] = []

    def add(label: str, url: Optional[str]) -> None:
        if url:
            links.append({"label": label, "url": url})

    add("Wikivoyage", (voyage or {}).get("page_url"))
    if wikidata_id:
        add(
            "Official site",
            fetch_wikidata_claim(wikidata_id, "P856", session=session),
        )
    name = destination.name.replace(" ", "_")
    add("Wikipedia", f"https://en.wikipedia.org/wiki/{name}")
    add("Wikimedia Commons", f"https://commons.wikimedia.org/wiki/Category:{name}")
    if destination.lat is not None and destination.lon is not None:
        add(
            "OpenStreetMap",
            f"https://www.openstreetmap.org/?mlat={destination.lat}&mlon={destination.lon}"
            f"#map=10/{destination.lat}/{destination.lon}",
        )
    for url in (voyage or {}).get("external_links", []):
        if url.startswith("http"):
            add(_domain_label(url), url)
    return _dedupe(links)[:MAX_LINKS]


def _books(destination: Destination, wikidata_id: str, session) -> list[dict]:
    books: list[dict] = []
    try:
        books += fetch_openlibrary_books(destination.name, session=session)
    except Exception:
        pass
    if wikidata_id:
        try:
            books += fetch_wikidata_narrative_works(wikidata_id, BOOK_TYPES, session=session)
        except Exception:
            pass
    return _dedupe(books, key="title")


def _films(wikidata_id: str, session) -> list[dict]:
    if not wikidata_id:
        return []
    try:
        return _dedupe(
            fetch_wikidata_narrative_works(wikidata_id, FILM_TYPES, session=session),
            key="title",
        )
    except Exception:
        return []


def _climate(destination: Destination, session) -> list[dict]:
    if destination.lat is None or destination.lon is None:
        return []
    try:
        return fetch_climate(destination.lat, destination.lon, session=session)
    except Exception:
        return []


def _diaries(destination: Destination, voyage, blogs) -> list[dict]:
    items: list[dict] = []
    for url in (voyage or {}).get("external_links", []) or []:
        if isinstance(url, str) and url.startswith("http"):
            items.append({"title": _domain_label(url), "url": url})
    for url in blogs or []:
        if isinstance(url, str) and url.startswith("http"):
            items.append({"title": _domain_label(url), "url": url})
    return _dedupe(items)[:MAX_DIARIES]


def _cluster_pois(pois: list[dict], days: int) -> list[list[dict]]:
    """Group points of interest into days by geographic proximity."""
    from wanderlens.core.taste import haversine_km

    located = [p for p in pois if p.get("lat") is not None and p.get("lon") is not None]
    unlocated = [p for p in pois if p not in located]
    if not located:
        return []
    per_day = max(1, (len(located) + days - 1) // days)
    remaining = list(located)
    plan: list[list[dict]] = []
    while remaining:
        current = [remaining.pop(0)]
        while remaining and len(current) < per_day:
            last = current[-1]
            nearest = min(
                remaining,
                key=lambda p: haversine_km(last["lat"], last["lon"], p["lat"], p["lon"]),
            )
            remaining.remove(nearest)
            current.append(nearest)
        plan.append(current)
    if unlocated and plan:
        plan[-1].extend(unlocated)
    elif unlocated:
        plan.append(unlocated)
    return plan


def _poi_itinerary(pois: list[dict], days: int) -> list[dict]:
    """Balance the Destination's points of interest across ``days`` days.

    Points are grouped by geographic proximity so a day stays in one area; when
    no coordinates are available, they are split evenly in order.
    """
    named = [poi for poi in pois if poi.get("name")]
    if not named:
        return []
    days = max(1, days)

    clustered = _cluster_pois(named, days)
    if clustered:
        groups = clustered
    else:
        per_day = max(1, (len(named) + days - 1) // days)
        groups = [named[index : index + per_day] for index in range(0, len(named), per_day)]

    return [
        {
            "title": f"Day {index}",
            "summary": "",
            "items": [poi["name"] for poi in group],
        }
        for index, group in enumerate(groups, start=1)
    ]


def _itineraries(destination, voyage, pois, synthesizer, days, search_results=None) -> list[dict]:
    itineraries: list[dict] = []
    for item in (voyage or {}).get("itineraries", []):
        itineraries.append(
            {
                "title": item.get("title", ""),
                "summary": "",
                "url": item.get("url", ""),
                "source": "wikivoyage",
                "days": [],
            }
        )
    synthesised: list[dict] = []
    if synthesizer is not None:
        try:
            synthesised = synthesizer.synthesize(
                destination, pois, days, search_results=search_results
            )
        except Exception:
            synthesised = []
        if synthesised:
            itineraries.append(
                {
                    "title": f"{destination.name} in {days} days",
                    "summary": "",
                    "url": "",
                    "source": "llm",
                    "model": getattr(synthesizer, "model", ""),
                    "prompt_version": getattr(synthesizer, "prompt_version", ""),
                    "days": synthesised,
                }
            )
    if not synthesised:
        plan = _poi_itinerary(pois, days)
        if plan:
            itineraries.append(
                {
                    "title": f"{destination.name} in {days} days",
                    "summary": "",
                    "url": "",
                    "source": "derived",
                    "days": plan,
                }
            )
    return itineraries


def store_guide(conn: sqlite3.Connection, destination_id: str, data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR REPLACE INTO destination_guide "
        "(destination_id, understand, links, books, pois, climate, films, diaries, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            destination_id,
            data.get("understand", ""),
            json.dumps(data.get("links", [])),
            json.dumps(data.get("books", [])),
            json.dumps(data.get("pois", [])),
            json.dumps(data.get("climate", [])),
            json.dumps(data.get("films", [])),
            json.dumps(data.get("diaries", [])),
            now,
        ),
    )
    conn.execute("DELETE FROM destination_itineraries WHERE destination_id = ?", (destination_id,))
    for position, itinerary in enumerate(data.get("itineraries", [])):
        conn.execute(
            "INSERT INTO destination_itineraries "
            "(destination_id, position, title, summary, days, source, model, prompt_version, url, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                destination_id,
                position,
                itinerary.get("title", ""),
                itinerary.get("summary", ""),
                json.dumps(itinerary.get("days", [])),
                itinerary.get("source", ""),
                itinerary.get("model", ""),
                itinerary.get("prompt_version", ""),
                itinerary.get("url", ""),
                now,
            ),
        )
    conn.commit()


def fetch_guide(
    conn: sqlite3.Connection,
    destination: Destination,
    session=None,
    synthesizer=None,
    days: int = DEFAULT_ITINERARY_DAYS,
    refresh: bool = False,
    blogs=None,
    searcher=None,
) -> bool:
    """Build and cache one guide. Returns whether it was (re)built."""
    if not refresh and is_guide_cached(conn, destination.id):
        return False
    data = gather_guide(
        destination, session=session, synthesizer=synthesizer, days=days, blogs=blogs, searcher=searcher
    )
    store_guide(conn, destination.id, data)
    return True


def build_guides_for(
    conn: sqlite3.Connection,
    destinations,
    session=None,
    synthesizer=None,
    days: int = DEFAULT_ITINERARY_DAYS,
    refresh: bool = False,
    blogs=None,
    searcher=None,
) -> int:
    built = 0
    for destination in destinations:
        try:
            if fetch_guide(
                conn,
                destination,
                session=session,
                synthesizer=synthesizer,
                days=days,
                refresh=refresh,
                blogs=blogs,
                searcher=searcher,
            ):
                built += 1
        except Exception:
            continue
    return built
