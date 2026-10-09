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
    PRIMARY KEY (user_id, run_id, rank)
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
