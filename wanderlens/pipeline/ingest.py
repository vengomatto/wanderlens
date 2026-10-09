from __future__ import annotations

import sqlite3

from wanderlens.config import Config
from wanderlens.core.models import Photo
from wanderlens.core.ports import PhotoSource
from wanderlens.db import connect, init_db
from wanderlens.sources.folder import FolderSource


def get_or_create_user(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
    if row:
        return int(row["id"])
    cur = conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    return int(cur.lastrowid)


def _store_photo(conn: sqlite3.Connection, user_id: int, photo: Photo) -> bool:
    exists = conn.execute(
        "SELECT 1 FROM photos WHERE user_id = ? AND source = ? AND sha256 = ?",
        (user_id, photo.source, photo.sha256),
    ).fetchone()
    if exists:
        return False
    conn.execute(
        """
        INSERT OR IGNORE INTO photos
            (user_id, id, source, path, sha256, taken_at, lat, lon, width, height)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            photo.id,
            photo.source,
            photo.path,
            photo.sha256,
            photo.taken_at.isoformat() if photo.taken_at else None,
            photo.lat,
            photo.lon,
            photo.width,
            photo.height,
        ),
    )
    return True


def run_ingest(
    config: Config,
    user_name: str = "owner",
    source: PhotoSource | None = None,
) -> int:
    config.ensure_dirs()
    conn = connect(config.db_path)
    init_db(conn)
    user_id = get_or_create_user(conn, user_name)
    source = source or FolderSource(config.photos_dir)

    added = 0
    for photo in source.iter_photos():
        if _store_photo(conn, user_id, photo):
            added += 1
    conn.commit()
    return added
