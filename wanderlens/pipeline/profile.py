from __future__ import annotations

import sqlite3
from datetime import datetime
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
        conn.execute(
            "INSERT INTO trips (user_id, id, start_at, end_at, country, city) VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                trip.id,
                min(times).isoformat() if times else None,
                max(times).isoformat() if times else None,
                trip.country,
                trip.city,
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


def _embed_photos(conn: sqlite3.Connection, user_id: int, photos: list[Photo], embedder) -> None:
    existing = {
        row[0]
        for row in conn.execute(
            "SELECT photo_id FROM photo_embeddings WHERE user_id = ?", (user_id,)
        )
    }
    for photo in photos:
        if photo.id in existing:
            continue
        vector = embedder.embed_image(photo.path)
        conn.execute(
            "INSERT OR REPLACE INTO photo_embeddings (user_id, photo_id, dim, vector) VALUES (?, ?, ?, ?)",
            (user_id, photo.id, int(vector.shape[0]), vector.astype("float32").tobytes()),
        )


def _store_subjects(
    conn: sqlite3.Connection, user_id: int, trips: list[Trip], vision, sample_per_trip: int
) -> None:
    counts: dict[str, float] = {}
    for trip in trips:
        sample = sample_trip_photos(trip.photos, sample_per_trip)
        try:
            tags = vision.describe([p.path for p in sample])
        except Exception:
            tags = []
        for tag in tags:
            counts[tag] = counts.get(tag, 0.0) + 1.0
    total = sum(counts.values())
    for tag, count in counts.items():
        conn.execute(
            "INSERT OR REPLACE INTO profile_entries (user_id, factor, key, value) VALUES (?, 'subjects', ?, ?)",
            (user_id, tag, count / total if total else 0.0),
        )


def run_profile(
    config: Config,
    user_name: str = "owner",
    embedder=None,
    vision=None,
    reverse_geocoder: Optional[ReverseGeocoder] = None,
    sample_per_trip: int = 3,
    retag: bool = False,
) -> list[Trip]:
    from wanderlens.pipeline.ingest import get_or_create_user

    config.ensure_dirs()
    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)

    photos = load_photos(conn, user_id)
    trips = to_trips(cluster_into_trips(photos), reverse_geocoder=reverse_geocoder or default_reverse_geocoder(config))

    _persist_trips(conn, user_id, trips)
    _store_geography(conn, user_id, trips)

    if embedder is None:
        from wanderlens.models.embeddings import OnnxClipEmbedder

        embedder = OnnxClipEmbedder(cache_dir=config.data_dir / "models")
    _embed_photos(conn, user_id, photos, embedder)

    if vision is not None:
        existing_subjects = conn.execute(
            "SELECT COUNT(*) FROM profile_entries WHERE user_id = ? AND factor = 'subjects'",
            (user_id,),
        ).fetchone()[0]
        if retag or existing_subjects == 0:
            _store_subjects(conn, user_id, trips, vision, sample_per_trip)

    conn.commit()
    return trips


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
