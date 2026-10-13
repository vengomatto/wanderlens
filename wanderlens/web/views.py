from __future__ import annotations

"""View models for the dashboard.

This is the seam between storage and HTTP: every function takes a connection
and plain identifiers and returns plain dataclasses. Route handlers do no SQL.
"""

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus

import numpy as np

from wanderlens.catalog.case import load_case
from wanderlens.pipeline.climate import load_destination_climate


def _structure(text: str) -> tuple[str, list[str]]:
    """Split prose into a lead sentence and highlight sentences for scannable display."""
    import re

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (text or "").strip()) if s.strip()]
    if not sentences:
        return "", []
    return sentences[0], sentences[1:5]


def record_feedback(conn: sqlite3.Connection, user_id: int, destination_id: str, action: str) -> None:
    from datetime import datetime, timezone

    if action not in {"save", "like", "dislike", "skip"}:
        return
    conn.execute(
        "INSERT OR REPLACE INTO feedback (user_id, destination_id, action, created_at) "
        "VALUES (?, ?, ?, ?)",
        (user_id, destination_id, action, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def feedback_action(conn: sqlite3.Connection, user_id: int, destination_id: str) -> str:
    row = conn.execute(
        "SELECT action FROM feedback WHERE user_id = ? AND destination_id = ?",
        (user_id, destination_id),
    ).fetchone()
    return row["action"] if row else ""


def external_photo_links(name: str, country: str = "") -> list[dict]:
    """Outbound photo searches — links only, never embedded proprietary images."""
    query = quote_plus(f"{name} {country}".strip())
    return [
        {"label": "Wikimedia Commons", "url": f"https://commons.wikimedia.org/w/index.php?search={query}"},
        {"label": "Getty Images", "url": f"https://www.gettyimages.com/photos/{query}"},
        {"label": "Google Images", "url": f"https://www.google.com/search?tbm=isch&q={query}"},
    ]


@dataclass
class TripView:
    id: int
    country: str
    city: str
    start_at: Optional[str]
    end_at: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    photo_count: int
    photo_ids: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        parts = [p for p in (self.city, self.country) if p]
        return ", ".join(parts) or f"Trip {self.id}"


@dataclass
class RecView:
    rank: int
    destination_id: str
    name: str
    country: str
    lat: Optional[float]
    lon: Optional[float]
    description: str
    score: float
    explanation: str
    embedding_score: Optional[float]
    attribute_score: Optional[float]
    has_image: bool = False
    score_pct: int = 0
    matched_attributes: list[tuple[str, float]] = field(default_factory=list)
    best_trip_label: str = ""
    nearest_trip_km: Optional[float] = None
    popularity_label: str = ""
    case_snippet: str = ""
    photo_links: list[dict] = field(default_factory=list)


@dataclass
class MediaImageRef:
    position: int
    filename: str
    source: str
    license: str
    attribution: str


@dataclass
class SimilarTrip:
    trip: TripView
    photo_ids: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class DestinationDetail:
    destination_id: str
    name: str
    country: str
    lat: Optional[float]
    lon: Optional[float]
    short_description: str = ""
    description_lead: str = ""
    description_highlights: list[str] = field(default_factory=list)
    explanation: str = ""
    score: Optional[float] = None
    embedding_score: Optional[float] = None
    attribute_score: Optional[float] = None
    title: str = ""
    page_url: str = ""
    extract: str = ""
    media_source: str = ""
    media_license: str = ""
    media_attribution: str = ""
    images: list[MediaImageRef] = field(default_factory=list)
    region_geojson: str = ""
    region_kind: str = ""
    region_radius_km: Optional[float] = None
    score_pct: int = 0
    matched_attributes: list[tuple[str, float]] = field(default_factory=list)
    best_trip_label: str = ""
    nearest_trip_km: Optional[float] = None
    popularity_label: str = ""
    understand: str = ""
    links: list[dict] = field(default_factory=list)
    books: list[dict] = field(default_factory=list)
    pois: list[dict] = field(default_factory=list)
    climate: list[dict] = field(default_factory=list)
    films: list[dict] = field(default_factory=list)
    itineraries: list[dict] = field(default_factory=list)
    similar_destinations: list[dict] = field(default_factory=list)
    case_narrative: str = ""
    case_sources: list[dict] = field(default_factory=list)
    case_source: str = ""
    diaries: list[dict] = field(default_factory=list)
    external_photo_links: list[dict] = field(default_factory=list)
    feedback_action: str = ""
    best_months: list[int] = field(default_factory=list)
    climate_match: float = 0.0


@dataclass
class PhotoView:
    id: str
    name: str


@dataclass
class MapPoint:
    kind: str
    label: str
    lat: float
    lon: float


@dataclass
class ProfileView:
    user_name: str
    geography: list[tuple[str, float]] = field(default_factory=list)
    subjects: list[tuple[str, float]] = field(default_factory=list)
    embedded_photos: int = 0
    trips: list[TripView] = field(default_factory=list)

    @property
    def has_profile(self) -> bool:
        return bool(self.geography or self.subjects or self.embedded_photos or self.trips)


def resolve_user(conn: sqlite3.Connection, name: str) -> Optional[int]:
    """Read-only user lookup; returns ``None`` if nothing has been persisted yet."""
    row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    return int(row["id"]) if row else None


def _matched_attributes(raw) -> list[tuple[str, float]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    return sorted(((k, float(v)) for k, v in data.items()), key=lambda item: -item[1])


def _json_list(raw) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _embedding(conn, destination_id):
    row = conn.execute(
        "SELECT vector FROM destination_embeddings WHERE destination_id = ? LIMIT 1",
        (destination_id,),
    ).fetchone()
    return np.frombuffer(row["vector"], dtype=np.float32) if row else None


def similar_destinations(
    conn: sqlite3.Connection, user_id: int, destination_id: str, limit: int = 4
) -> list[dict]:
    base = _embedding(conn, destination_id)
    if base is None:
        return []
    base_norm = float(np.linalg.norm(base)) or 1.0
    scored: list[tuple[float, dict]] = []
    rows = conn.execute(
        "SELECT destination_id, destination_name, destination_country FROM recommendations "
        "WHERE user_id = ? AND destination_id <> ? ORDER BY rank",
        (user_id, destination_id),
    ).fetchall()
    for row in rows:
        vector = _embedding(conn, row["destination_id"])
        if vector is None:
            continue
        denom = base_norm * (float(np.linalg.norm(vector)) or 1.0)
        scored.append(
            (
                float(np.dot(base, vector)) / denom,
                {
                    "id": row["destination_id"],
                    "name": row["destination_name"] or row["destination_id"],
                    "country": row["destination_country"] or "",
                },
            )
        )
    scored.sort(key=lambda item: -item[0])
    return [item for _, item in scored[:limit]]


def trips_view(conn: sqlite3.Connection, user_id: int) -> list[TripView]:
    rows = conn.execute(
        "SELECT id, start_at, end_at, country, city, lat, lon FROM trips "
        "WHERE user_id = ? ORDER BY start_at IS NULL, start_at DESC, id DESC",
        (user_id,),
    ).fetchall()
    photos: dict[int, list[str]] = {}
    for row in conn.execute(
        "SELECT tp.trip_id AS trip_id, tp.photo_id AS photo_id FROM trip_photos tp "
        "JOIN photos p ON p.user_id = tp.user_id AND p.id = tp.photo_id "
        "WHERE tp.user_id = ? ORDER BY p.taken_at IS NULL, p.taken_at",
        (user_id,),
    ):
        photos.setdefault(row["trip_id"], []).append(row["photo_id"])
    attributes: dict[int, list[str]] = {}
    for row in conn.execute(
        "SELECT trip_id, subject FROM trip_subjects WHERE user_id = ? ORDER BY subject",
        (user_id,),
    ):
        attributes.setdefault(row["trip_id"], []).append(row["subject"])

    return [
        TripView(
            id=row["id"],
            country=row["country"] or "",
            city=row["city"] or "",
            start_at=row["start_at"],
            end_at=row["end_at"],
            lat=row["lat"],
            lon=row["lon"],
            photo_count=len(photos.get(row["id"], [])),
            photo_ids=photos.get(row["id"], []),
            attributes=attributes.get(row["id"], []),
        )
        for row in rows
    ]


def profile_view(conn: sqlite3.Connection, name: str) -> ProfileView:
    user_id = resolve_user(conn, name)
    if user_id is None:
        return ProfileView(user_name=name)

    entries = conn.execute(
        "SELECT factor, key, value FROM profile_entries WHERE user_id = ? ORDER BY value DESC",
        (user_id,),
    ).fetchall()
    embedded = conn.execute(
        "SELECT COUNT(*) FROM photo_embeddings WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    return ProfileView(
        user_name=name,
        geography=[(r["key"], r["value"]) for r in entries if r["factor"] == "geography"],
        subjects=[(r["key"], r["value"]) for r in entries if r["factor"] == "subjects"],
        embedded_photos=int(embedded),
        trips=trips_view(conn, user_id),
    )


def trip_detail(conn: sqlite3.Connection, user_id: int, trip_id: int) -> Optional[dict]:
    trip = next((t for t in trips_view(conn, user_id) if t.id == trip_id), None)
    if trip is None:
        return None
    rows = conn.execute(
        "SELECT p.id AS id, p.path AS path FROM trip_photos tp "
        "JOIN photos p ON p.user_id = tp.user_id AND p.id = tp.photo_id "
        "WHERE tp.user_id = ? AND tp.trip_id = ? ORDER BY p.taken_at IS NULL, p.taken_at",
        (user_id, trip_id),
    ).fetchall()
    photos = [PhotoView(id=r["id"], name=Path(r["path"]).name) for r in rows]
    return {"trip": trip, "photos": photos, "attributes": trip.attributes}


def recommendations_view(conn: sqlite3.Connection, user_id: int) -> list[RecView]:
    rows = conn.execute(
        "SELECT rank, destination_id, destination_name, destination_country, "
        "destination_lat, destination_lon, destination_description, score, "
        "explanation, embedding_score, attribute_score, matched_attributes, "
        "best_trip_label, nearest_trip_km, popularity_label "
        "FROM recommendations WHERE user_id = ? ORDER BY rank",
        (user_id,),
    ).fetchall()
    with_images = _destinations_with_images(conn, [row["destination_id"] for row in rows])
    return [
        RecView(
            rank=row["rank"],
            destination_id=row["destination_id"],
            name=row["destination_name"] or row["destination_id"],
            country=row["destination_country"] or "",
            lat=row["destination_lat"],
            lon=row["destination_lon"],
            description=row["destination_description"] or "",
            score=row["score"],
            explanation=row["explanation"] or "",
            embedding_score=row["embedding_score"],
            attribute_score=row["attribute_score"],
            has_image=row["destination_id"] in with_images,
            score_pct=int(round(max(0.0, min(1.0, row["score"])) * 100)),
            matched_attributes=_matched_attributes(row["matched_attributes"]),
            best_trip_label=row["best_trip_label"] or "",
            nearest_trip_km=row["nearest_trip_km"],
            popularity_label=row["popularity_label"] or "",
            case_snippet=_case_snippet(conn, row["destination_id"]),
            photo_links=external_photo_links(
                row["destination_name"] or row["destination_id"],
                row["destination_country"] or "",
            ),
        )
        for row in rows
    ]


def _case_snippet(conn: sqlite3.Connection, destination_id: str, limit: int = 180) -> str:
    case = load_case(conn, destination_id)
    if not case or not case.get("narrative"):
        return ""
    narrative = case["narrative"].strip()
    if len(narrative) <= limit:
        return narrative
    return narrative[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


def _destinations_with_images(conn: sqlite3.Connection, destination_ids: list[str]) -> set[str]:
    ids = [i for i in destination_ids if i]
    if not ids:
        return set()
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT DISTINCT destination_id FROM destination_images "
        f"WHERE destination_id IN ({placeholders})",
        ids,
    )
    return {row["destination_id"] for row in rows}


def destination_detail(
    conn: sqlite3.Connection, user_id: int, destination_id: str
) -> Optional[DestinationDetail]:
    rec = conn.execute(
        "SELECT destination_name, destination_country, destination_lat, destination_lon, "
        "destination_description, score, explanation, embedding_score, attribute_score, "
        "matched_attributes, best_trip_label, nearest_trip_km, popularity_label "
        "FROM recommendations WHERE user_id = ? AND destination_id = ? "
        "ORDER BY run_id DESC, rank LIMIT 1",
        (user_id, destination_id),
    ).fetchone()
    media = conn.execute(
        "SELECT title, page_url, extract, source, license, attribution, region_geojson, "
        "region_kind, region_radius_km FROM destination_media WHERE destination_id = ?",
        (destination_id,),
    ).fetchone()
    if rec is None and media is None:
        return None

    images = [
        MediaImageRef(
            position=row["position"],
            filename=row["filename"],
            source=row["source"] or "",
            license=row["license"] or "",
            attribution=row["attribution"] or "",
        )
        for row in conn.execute(
            "SELECT position, filename, source, license, attribution FROM destination_images "
            "WHERE destination_id = ? ORDER BY position",
            (destination_id,),
        )
    ]

    guide = conn.execute(
        "SELECT understand, links, books, pois, climate, films, diaries FROM destination_guide "
        "WHERE destination_id = ?",
        (destination_id,),
    ).fetchone()
    itineraries = [
        {
            "title": row["title"] or "",
            "summary": row["summary"] or "",
            "days": _json_list(row["days"]),
            "source": row["source"] or "",
            "model": row["model"] or "",
            "url": row["url"] or "",
        }
        for row in conn.execute(
            "SELECT title, summary, days, source, model, url FROM destination_itineraries "
            "WHERE destination_id = ? ORDER BY position",
            (destination_id,),
        )
    ]

    case = load_case(conn, destination_id) or {}
    climate_fit = load_destination_climate(conn, destination_id)
    name = (rec["destination_name"] if rec else "") or destination_id
    country = (rec["destination_country"] if rec else "") or ""
    description_text = (
        (guide["understand"] if guide else "")
        or (media["extract"] if media else "")
        or ((rec["destination_description"] if rec else "") or "")
    )
    description_lead, description_highlights = _structure(description_text)

    return DestinationDetail(
        destination_id=destination_id,
        name=name,
        country=country,
        case_narrative=(case.get("narrative") or ""),
        case_sources=(case.get("sources") or []),
        case_source=(case.get("source") or ""),
        feedback_action=feedback_action(conn, user_id, destination_id),
        best_months=climate_fit.get("best_months", []),
        climate_match=climate_fit.get("match", 0.0),
        description_lead=description_lead,
        description_highlights=description_highlights,
        diaries=_json_list(guide["diaries"]) if guide and "diaries" in guide.keys() else [],
        external_photo_links=external_photo_links(name, country),
        lat=rec["destination_lat"] if rec else None,
        lon=rec["destination_lon"] if rec else None,
        short_description=(rec["destination_description"] if rec else "") or "",
        explanation=(rec["explanation"] if rec else "") or "",
        score=rec["score"] if rec else None,
        embedding_score=rec["embedding_score"] if rec else None,
        attribute_score=rec["attribute_score"] if rec else None,
        title=(media["title"] if media else "") or "",
        page_url=(media["page_url"] if media else "") or "",
        extract=(media["extract"] if media else "") or "",
        media_source=(media["source"] if media else "") or "",
        media_license=(media["license"] if media else "") or "",
        media_attribution=(media["attribution"] if media else "") or "",
        images=images,
        region_geojson=(media["region_geojson"] if media else "") or "",
        region_kind=(media["region_kind"] if media else "") or "",
        region_radius_km=media["region_radius_km"] if media else None,
        score_pct=int(round(max(0.0, min(1.0, rec["score"])) * 100)) if rec else 0,
        matched_attributes=_matched_attributes(rec["matched_attributes"]) if rec else [],
        best_trip_label=(rec["best_trip_label"] if rec else "") or "",
        nearest_trip_km=rec["nearest_trip_km"] if rec else None,
        popularity_label=(rec["popularity_label"] if rec else "") or "",
        understand=(guide["understand"] if guide else "") or "",
        links=_json_list(guide["links"]) if guide else [],
        books=_json_list(guide["books"]) if guide else [],
        pois=_json_list(guide["pois"]) if guide else [],
        climate=_json_list(guide["climate"]) if guide else [],
        films=_json_list(guide["films"]) if guide else [],
        itineraries=itineraries,
        similar_destinations=similar_destinations(conn, user_id, destination_id),
    )


def similar_trips(
    conn: sqlite3.Connection,
    user_id: int,
    destination_id: str,
    limit: int = 3,
    photos_per_trip: int = 3,
) -> list[SimilarTrip]:
    dest_row = conn.execute(
        "SELECT vector FROM destination_embeddings WHERE destination_id = ? LIMIT 1",
        (destination_id,),
    ).fetchone()
    if dest_row is None:
        return []
    dest_vector = np.frombuffer(dest_row["vector"], dtype=np.float32)

    rows = conn.execute(
        "SELECT tp.trip_id AS trip_id, pe.vector AS vector FROM trip_photos tp "
        "JOIN photo_embeddings pe ON pe.user_id = tp.user_id AND pe.photo_id = tp.photo_id "
        "WHERE tp.user_id = ?",
        (user_id,),
    ).fetchall()
    groups: dict[int, list[np.ndarray]] = {}
    for row in rows:
        groups.setdefault(row["trip_id"], []).append(
            np.frombuffer(row["vector"], dtype=np.float32)
        )

    scored: list[tuple[float, int]] = []
    for trip_id, vectors in groups.items():
        mean = np.mean(np.stack(vectors), axis=0).astype(np.float32)
        norm = float(np.linalg.norm(mean))
        if norm:
            mean = mean / norm
        scored.append((float(np.dot(mean, dest_vector)), trip_id))
    scored.sort(key=lambda item: -item[0])
    scored = [item for item in scored if item[0] > 0][:limit]
    if not scored:
        return []

    trips = {trip.id: trip for trip in trips_view(conn, user_id)}
    results: list[SimilarTrip] = []
    for score, trip_id in scored:
        if trip_id not in trips:
            continue
        photo_rows = conn.execute(
            "SELECT p.id AS id FROM trip_photos tp "
            "JOIN photos p ON p.user_id = tp.user_id AND p.id = tp.photo_id "
            "WHERE tp.user_id = ? AND tp.trip_id = ? ORDER BY p.taken_at IS NULL, p.taken_at "
            "LIMIT ?",
            (user_id, trip_id, photos_per_trip),
        ).fetchall()
        results.append(
            SimilarTrip(
                trip=trips[trip_id],
                photo_ids=[r["id"] for r in photo_rows],
                score=score,
            )
        )
    return results


def map_points(conn: sqlite3.Connection, user_id: int) -> list[MapPoint]:
    points: list[MapPoint] = []
    for trip in trips_view(conn, user_id):
        if trip.lat is not None and trip.lon is not None:
            points.append(MapPoint(kind="trip", label=trip.label, lat=trip.lat, lon=trip.lon))
    for rec in recommendations_view(conn, user_id):
        if rec.lat is not None and rec.lon is not None:
            points.append(MapPoint(kind="destination", label=rec.name, lat=rec.lat, lon=rec.lon))
    return points
