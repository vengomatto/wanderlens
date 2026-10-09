from wanderlens.db import connect, init_db

CORE_TABLES = {"users", "photos", "trips", "profile_entries", "recommendations"}
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
