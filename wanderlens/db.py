from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id      INTEGER PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS photos (
    user_id     INTEGER NOT NULL,
    id          TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    path        TEXT    NOT NULL,
    sha256      TEXT    NOT NULL,
    taken_at    TEXT,
    lat         REAL,
    lon         REAL,
    width       INTEGER,
    height      INTEGER,
    PRIMARY KEY (user_id, id)
);

CREATE TABLE IF NOT EXISTS photo_embeddings (
    user_id     INTEGER NOT NULL,
    photo_id    TEXT    NOT NULL,
    dim         INTEGER NOT NULL,
    vector      BLOB    NOT NULL,
    PRIMARY KEY (user_id, photo_id)
);

CREATE TABLE IF NOT EXISTS destination_embeddings (
    destination_id  TEXT    NOT NULL,
    model           TEXT    NOT NULL,
    dim             INTEGER NOT NULL,
    vector          BLOB    NOT NULL,
    PRIMARY KEY (destination_id, model)
);

CREATE TABLE IF NOT EXISTS trips (
    user_id     INTEGER NOT NULL,
    id          INTEGER NOT NULL,
    start_at    TEXT,
    end_at      TEXT,
    country     TEXT,
    city        TEXT,
    lat         REAL,
    lon         REAL,
    PRIMARY KEY (user_id, id)
);

CREATE TABLE IF NOT EXISTS trip_photos (
    user_id     INTEGER NOT NULL,
    trip_id     INTEGER NOT NULL,
    photo_id    TEXT    NOT NULL,
    PRIMARY KEY (user_id, trip_id, photo_id)
);

CREATE TABLE IF NOT EXISTS trip_subjects (
    user_id     INTEGER NOT NULL,
    trip_id     INTEGER NOT NULL,
    subject     TEXT    NOT NULL,
    PRIMARY KEY (user_id, trip_id, subject)
);

CREATE TABLE IF NOT EXISTS profile_entries (
    user_id     INTEGER NOT NULL,
    factor      TEXT    NOT NULL,
    key         TEXT    NOT NULL,
    value       REAL    NOT NULL,
    PRIMARY KEY (user_id, factor, key)
);

CREATE TABLE IF NOT EXISTS recommendations (
    user_id         INTEGER NOT NULL,
    run_id          INTEGER NOT NULL,
    rank            INTEGER NOT NULL,
    destination_id  TEXT    NOT NULL,
    score           REAL    NOT NULL,
    explanation     TEXT,
    destination_name        TEXT,
    destination_country     TEXT,
    destination_lat         REAL,
    destination_lon         REAL,
    destination_description TEXT,
    embedding_score         REAL,
    attribute_score         REAL,
    matched_attributes      TEXT,
    best_trip_id            INTEGER,
    best_trip_label         TEXT,
    best_facet_similarity   REAL,
    nearest_trip_km         REAL,
    popularity              REAL,
    popularity_label        TEXT,
    PRIMARY KEY (user_id, run_id, rank)
);

CREATE TABLE IF NOT EXISTS recommendation_explanations (
    user_id         INTEGER NOT NULL,
    destination_id  TEXT    NOT NULL,
    evidence_hash   TEXT    NOT NULL,
    model           TEXT,
    prompt_version  TEXT,
    text            TEXT    NOT NULL,
    created_at      TEXT,
    PRIMARY KEY (user_id, destination_id, evidence_hash)
);

CREATE TABLE IF NOT EXISTS destination_media (
    destination_id   TEXT PRIMARY KEY,
    title            TEXT,
    page_url         TEXT,
    extract          TEXT,
    source           TEXT,
    license          TEXT,
    attribution      TEXT,
    region_geojson   TEXT,
    region_kind      TEXT,
    region_radius_km REAL,
    fetched_at       TEXT
);

CREATE TABLE IF NOT EXISTS destination_images (
    destination_id  TEXT    NOT NULL,
    position        INTEGER NOT NULL,
    filename        TEXT    NOT NULL,
    source          TEXT,
    license         TEXT,
    attribution     TEXT,
    PRIMARY KEY (destination_id, position)
);

CREATE TABLE IF NOT EXISTS destination_popularity (
    destination_id  TEXT PRIMARY KEY,
    pageviews       INTEGER,
    score           REAL,
    fetched_at      TEXT
);

CREATE TABLE IF NOT EXISTS taste_enrichment (
    user_id         INTEGER NOT NULL,
    kind            TEXT    NOT NULL,
    ref_id          TEXT    NOT NULL,
    input_hash      TEXT    NOT NULL,
    model           TEXT,
    prompt_version  TEXT,
    result          TEXT    NOT NULL,
    created_at      TEXT,
    PRIMARY KEY (user_id, kind, ref_id, input_hash)
);

CREATE TABLE IF NOT EXISTS destination_case (
    destination_id  TEXT    NOT NULL,
    input_hash      TEXT    NOT NULL,
    model           TEXT,
    prompt_version  TEXT,
    narrative       TEXT,
    sources         TEXT,
    source          TEXT,
    fetched_at      TEXT,
    PRIMARY KEY (destination_id, input_hash)
);

CREATE TABLE IF NOT EXISTS feedback (
    user_id         INTEGER NOT NULL,
    destination_id  TEXT    NOT NULL,
    action          TEXT    NOT NULL,
    created_at      TEXT,
    PRIMARY KEY (user_id, destination_id)
);

CREATE TABLE IF NOT EXISTS trip_weather (
    user_id     INTEGER NOT NULL,
    trip_id     INTEGER NOT NULL,
    temp_c      REAL,
    precip_mm   REAL,
    month       INTEGER,
    fetched_at  TEXT,
    PRIMARY KEY (user_id, trip_id)
);

CREATE TABLE IF NOT EXISTS tag_cache (
    user_id         INTEGER NOT NULL,
    input_hash      TEXT    NOT NULL,
    model           TEXT,
    prompt_version  TEXT,
    tags            TEXT,
    created_at      TEXT,
    PRIMARY KEY (user_id, input_hash)
);

CREATE TABLE IF NOT EXISTS destination_climate (
    destination_id  TEXT PRIMARY KEY,
    climate         TEXT,
    best_months     TEXT,
    match           REAL,
    fetched_at      TEXT
);

CREATE TABLE IF NOT EXISTS destination_guide (
    destination_id  TEXT PRIMARY KEY,
    understand      TEXT,
    links           TEXT,
    books           TEXT,
    pois            TEXT,
    climate         TEXT,
    films           TEXT,
    diaries         TEXT,
    fetched_at      TEXT
);

CREATE TABLE IF NOT EXISTS destination_itineraries (
    destination_id  TEXT    NOT NULL,
    position        INTEGER NOT NULL,
    title           TEXT,
    summary         TEXT,
    days            TEXT,
    source          TEXT,
    model           TEXT,
    prompt_version  TEXT,
    url             TEXT,
    fetched_at      TEXT,
    PRIMARY KEY (destination_id, position)
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    _migrate(conn)
    conn.commit()


def _migrate(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(trips)")}
    if "lat" not in columns:
        conn.execute("ALTER TABLE trips ADD COLUMN lat REAL")
    if "lon" not in columns:
        conn.execute("ALTER TABLE trips ADD COLUMN lon REAL")

    rec_columns = {row[1] for row in conn.execute("PRAGMA table_info(recommendations)")}
    for column, declaration in (
        ("destination_name", "TEXT"),
        ("destination_country", "TEXT"),
        ("destination_lat", "REAL"),
        ("destination_lon", "REAL"),
        ("destination_description", "TEXT"),
        ("embedding_score", "REAL"),
        ("attribute_score", "REAL"),
        ("matched_attributes", "TEXT"),
        ("best_trip_id", "INTEGER"),
        ("best_trip_label", "TEXT"),
        ("best_facet_similarity", "REAL"),
        ("nearest_trip_km", "REAL"),
        ("popularity", "REAL"),
        ("popularity_label", "TEXT"),
    ):
        if column not in rec_columns:
            conn.execute(f"ALTER TABLE recommendations ADD COLUMN {column} {declaration}")

    guide_columns = {row[1] for row in conn.execute("PRAGMA table_info(destination_guide)")}
    if "diaries" not in guide_columns:
        conn.execute("ALTER TABLE destination_guide ADD COLUMN diaries TEXT")
