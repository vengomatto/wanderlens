from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Callable, Optional

from wanderlens.config import Config
from wanderlens.core.models import Photo, Trip
from wanderlens.core.taste import cluster_into_trips, geography_weights, to_trips
from wanderlens.db import connect, init_db

ReverseGeocoder = Callable[[float, float], Optional[tuple[str, str]]]


def load_photos(conn: sqlite3.Connection, user_id: int) -> list[Photo]:
    rows = conn.execute("SELECT * FROM photos WHERE user_id = ?", (user_id,)).fetchall()
    photos = []
    for row in rows:
        taken = datetime.fromisoformat(row["taken_at"]) if row["taken_at"] else None
        photos.append(
            Photo(
                id=row["id"],
                source=row["source"],
                path=row["path"],
                sha256=row["sha256"],
                taken_at=taken,
                lat=row["lat"],
                lon=row["lon"],
                width=row["width"],
                height=row["height"],
            )
        )
    return photos


def sample_trip_photos(photos: list[Photo], count: int) -> list[Photo]:
    ordered = sorted(photos, key=lambda p: p.taken_at or datetime.min)
    if len(ordered) <= count:
        return ordered
    step = len(ordered) / count
    return [ordered[int(i * step)] for i in range(count)]


def default_reverse_geocoder(config: Config) -> Optional[ReverseGeocoder]:
    from wanderlens.catalog.geonames import GeoNamesIndex

    cities = config.catalog_path / "cities500.txt"
    countries = config.catalog_path / "countryInfo.txt"
    if not cities.exists():
        return None
    index = GeoNamesIndex(cities, countries if countries.exists() else None)
    return lambda lat, lon: index.nearest(lat, lon)


def _persist_trips(conn: sqlite3.Connection, user_id: int, trips: list[Trip]) -> None:
    conn.execute("DELETE FROM trips WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM trip_photos WHERE user_id = ?", (user_id,))
    for trip in trips:
        times = [p.taken_at for p in trip.photos if p.taken_at]
        located = [p for p in trip.photos if p.lat is not None and p.lon is not None]
        lat = sum(p.lat for p in located) / len(located) if located else None
        lon = sum(p.lon for p in located) / len(located) if located else None
        conn.execute(
            "INSERT INTO trips (user_id, id, start_at, end_at, country, city, lat, lon) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user_id,
                trip.id,
                min(times).isoformat() if times else None,
                max(times).isoformat() if times else None,
                trip.country,
                trip.city,
                lat,
                lon,
            ),
        )
        for photo in trip.photos:
            conn.execute(
                "INSERT OR IGNORE INTO trip_photos (user_id, trip_id, photo_id) VALUES (?, ?, ?)",
                (user_id, trip.id, photo.id),
            )


def _store_geography(conn: sqlite3.Connection, user_id: int, trips: list[Trip]) -> None:
    for country, weight in geography_weights(trips).items():
        conn.execute(
            "INSERT OR REPLACE INTO profile_entries (user_id, factor, key, value) VALUES (?, 'geography', ?, ?)",
            (user_id, country, weight),
        )


def _embed_photos(conn: sqlite3.Connection, user_id: int, photos: list[Photo], embedder) -> int:
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT photo_id FROM photo_embeddings WHERE user_id = ?", (user_id,)
        )
    }
    skipped = 0
    for photo in photos:
        if photo.id in existing:
            continue
        try:
            vector = embedder.embed_image(photo.path)
        except Exception:
            skipped += 1
            continue
        conn.execute(
            "INSERT OR REPLACE INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (?, ?, ?, ?)",
            (user_id, photo.id, int(vector.shape[0]), vector.astype("float32").tobytes()),
        )
    return skipped


def _store_subjects(
    conn: sqlite3.Connection,
    user_id: int,
    trips: list[Trip],
    vision,
    sample_per_trip: int,
    enricher=None,
    retag: bool = False,
) -> None:
    import hashlib
    import json
    from collections import Counter
    from datetime import datetime, timezone

    from wanderlens.core.vocabulary import canonicalize
    from wanderlens.pipeline.enrichment import enrich_trip_attributes

    conn.execute("DELETE FROM trip_subjects WHERE user_id = ?", (user_id,))
    conn.execute(
        "DELETE FROM profile_entries WHERE user_id = ? AND factor = 'subjects'", (user_id,)
    )

    model = getattr(vision, "model", "")
    prompt = getattr(vision, "prompt_version", "vision-v1")
    per_trip: dict[int, set[str]] = {}
    for trip in trips:
        sample = sample_trip_photos(trip.photos, sample_per_trip)
        digest = hashlib.sha256(
            "|".join(sorted(p.sha256 for p in sample)).encode()
        ).hexdigest()
        tags = None
        if not retag:
            row = conn.execute(
                "SELECT tags FROM tag_cache WHERE user_id = ? AND input_hash = ?",
                (user_id, digest),
            ).fetchone()
            if row is not None:
                try:
                    tags = json.loads(row["tags"])
                except (ValueError, TypeError):
                    tags = None
        if tags is None:
            try:
                tags = vision.describe([p.path for p in sample])
            except Exception:
                tags = []
            conn.execute(
                "INSERT OR REPLACE INTO tag_cache "
                "(user_id, input_hash, model, prompt_version, tags, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    digest,
                    model,
                    prompt,
                    json.dumps(tags),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        attributes: set[str] = set()
        for tag in tags:
            attributes.update(canonicalize(tag))
        context = ", ".join(p for p in (trip.city, trip.country) if p)
        for attribute in enrich_trip_attributes(conn, user_id, trip.id, tags, enricher, context):
            attributes.update(canonicalize(attribute))
        per_trip[trip.id] = attributes
        for attribute in sorted(attributes):
            conn.execute(
                "INSERT OR IGNORE INTO trip_subjects (user_id, trip_id, subject) VALUES (?, ?, ?)",
                (user_id, trip.id, attribute),
            )

    total_trips = len(trips) or 1
    recurrence: Counter = Counter()
    for attributes in per_trip.values():
        for attribute in attributes:
            recurrence[attribute] += 1
    for attribute, count in recurrence.items():
        conn.execute(
            "INSERT OR REPLACE INTO profile_entries (user_id, factor, key, value) "
            "VALUES (?, 'subjects', ?, ?)",
            (user_id, attribute, count / total_trips),
        )


def run_profile(
    config: Config,
    user_name: str = "owner",
    embedder=None,
    vision=None,
    reverse_geocoder: Optional[ReverseGeocoder] = None,
    sample_per_trip: int = 3,
    retag: bool = False,
    enricher=None,
    stats: Optional[dict] = None,
) -> list[Trip]:
    from wanderlens.pipeline.ingest import get_or_create_user

    config.ensure_dirs()
    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    photos = load_photos(conn, user_id)
    clusters = cluster_into_trips(
        photos,
        max_gap=timedelta(hours=getattr(config, "split_gap_hours", 18.0)),
        max_jump_km=getattr(config, "split_jump_km", 150.0),
    )
    trips = to_trips(clusters, reverse_geocoder=reverse_geocoder or default_reverse_geocoder(config))

    _persist_trips(conn, user_id, trips)
    _store_geography(conn, user_id, trips)

    if embedder is None:
        from wanderlens.models.embeddings import OnnxClipEmbedder

        embedder = OnnxClipEmbedder(cache_dir=config.data_dir / "models")
    skipped = _embed_photos(conn, user_id, photos, embedder)
    if stats is not None:
        stats["photos_skipped"] = skipped

    if vision is not None:
        _store_subjects(
            conn, user_id, trips, vision, sample_per_trip, enricher, retag=retag
        )

    conn.commit()
    return trips


def estimate_tagging(config: Config, user_name: str = "owner", sample_per_trip: int = 3) -> str:
    """A dry-run: how many images tagging would send and a rough cost estimate."""
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)
    photos = load_photos(conn, user_id)
    trips = cluster_into_trips(photos)
    images = sum(len(sample_trip_photos(trip, sample_per_trip)) for trip in trips)
    estimated_usd = images * 1500 / 1_000_000 * 0.15
    return (
        f"Tagging would send {images} image(s) across {len(trips)} trip(s); "
        f"estimated cost ≈ ${estimated_usd:.4f} (low detail, approximate)."
    )


def show_profile(config: Config, user_name: str = "owner") -> str:
    from wanderlens.pipeline.ingest import get_or_create_user

    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    rows = conn.execute(
        "SELECT factor, key, value FROM profile_entries WHERE user_id = ? ORDER BY factor, value DESC",
        (user_id,),
    ).fetchall()
    embedded = conn.execute(
        "SELECT COUNT(*) FROM photo_embeddings WHERE user_id = ?", (user_id,)
    ).fetchone()[0]
    trips = conn.execute("SELECT COUNT(*) FROM trips WHERE user_id = ?", (user_id,)).fetchone()[0]

    if not rows and not embedded:
        return "No taste profile yet. Run `wanderlens ingest` first."

    geography = [r for r in rows if r["factor"] == "geography"]
    subjects = [r for r in rows if r["factor"] == "subjects"]

    lines = ["Taste Profile", f"Trips: {trips}    Photos embedded: {embedded}"]
    lines.append("Visited geography:")
    lines += [f"  {r['key']}: {r['value']:.2f}" for r in geography] or ["  (none)"]
    lines.append(f"Aesthetics: visual embeddings for {embedded} photo(s)")
    lines.append("Subjects / activities:")
    lines += [f"  {r['key']}: {r['value']:.2f}" for r in subjects] or ["  (none — run with tagging)"]
    return "\n".join(lines)
