import sqlite3

from wanderlens.db import connect, init_db

CORE_TABLES = {"users", "photos", "trips", "profile_entries", "recommendations"}
MEDIA_TABLES = {"destination_media", "destination_images"}
SCOPED_TABLES = {
    "photos",
    "photo_embeddings",
    "trips",
    "trip_photos",
    "profile_entries",
    "recommendations",
}


def test_schema_creates_core_tables(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)

    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert CORE_TABLES <= names


def test_every_scoped_table_has_user_id(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)

    for table in SCOPED_TABLES:
        columns = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        assert "user_id" in columns, f"{table} is missing user_id"


def test_schema_creates_media_tables(tmp_path):
    conn = connect(tmp_path / "wl.sqlite3")
    init_db(conn)

    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert MEDIA_TABLES <= names

    media_cols = {r[1] for r in conn.execute("PRAGMA table_info(destination_media)")}
    assert {
        "page_url",
        "extract",
        "source",
        "license",
        "attribution",
        "region_geojson",
        "region_kind",
        "region_radius_km",
        "fetched_at",
    } <= media_cols

    image_cols = {r[1] for r in conn.execute("PRAGMA table_info(destination_images)")}
    assert {"destination_id", "position", "filename", "license", "attribution"} <= image_cols
    assert "user_id" not in image_cols  # catalog-scoped, not user-scoped


def test_media_tables_added_to_legacy_db(tmp_path):
    db = tmp_path / "old.sqlite3"
    legacy = sqlite3.connect(db)
    legacy.execute(
        "CREATE TABLE recommendations ("
        "user_id INTEGER, run_id INTEGER, rank INTEGER, destination_id TEXT, "
        "score REAL, explanation TEXT, PRIMARY KEY (user_id, run_id, rank))"
    )
    legacy.commit()
    legacy.close()

    conn = connect(db)
    init_db(conn)

    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert MEDIA_TABLES <= names


def test_migrate_adds_recommendation_display_columns(tmp_path):
    db = tmp_path / "old.sqlite3"
    legacy = sqlite3.connect(db)
    legacy.execute(
        "CREATE TABLE recommendations ("
        "user_id INTEGER, run_id INTEGER, rank INTEGER, destination_id TEXT, "
        "score REAL, explanation TEXT, PRIMARY KEY (user_id, run_id, rank))"
    )
    legacy.commit()
    legacy.close()

    conn = connect(db)
    init_db(conn)

    columns = {r[1] for r in conn.execute("PRAGMA table_info(recommendations)")}
    assert {
        "destination_name",
        "destination_country",
        "destination_lat",
        "destination_lon",
        "destination_description",
        "embedding_score",
        "attribute_score",
    } <= columns
