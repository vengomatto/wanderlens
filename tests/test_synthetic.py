from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.sources.folder import FolderSource
from wanderlens.synthetic import SyntheticVision, materialize, seed_profile


def test_materialize_is_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    materialize(a, trips_per_taste=2, destinations_per_taste=3, photos_per_trip=2)
    materialize(b, trips_per_taste=2, destinations_per_taste=3, photos_per_trip=2)

    assert (a / "catalog" / "destinations.json").read_bytes() == (
        b / "catalog" / "destinations.json"
    ).read_bytes()
    assert sorted(p.name for p in (a / "photos").iterdir()) == sorted(
        p.name for p in (b / "photos").iterdir()
    )


def test_materialize_archive_reads_back(tmp_path):
    target = tmp_path / "syn"
    counts = materialize(
        target, trips_per_taste=2, destinations_per_taste=3, photos_per_trip=3
    )

    catalog = JsonCatalog.load(target / "catalog" / "destinations.json")
    assert len(catalog.candidates()) == counts["destinations"]

    photos = list(FolderSource(target / "photos").iter_photos())
    assert len(photos) == counts["photos"]
    assert all(photo.taken_at and photo.lat is not None and photo.lon is not None for photo in photos)


def test_synthetic_vision_tags_by_cluster():
    tags = SyntheticVision().describe(["/x/coastal_01_00.jpg", "/x/mountain_02_01.jpg"])
    assert "coastal" in tags
    assert "mountains" in tags


def test_seed_profile_creates_tagged_subjects(tmp_path):
    import sqlite3

    target = tmp_path / "syn"
    materialize(target, trips_per_taste=2, destinations_per_taste=3, photos_per_trip=3)

    trips = seed_profile(target)

    assert trips >= 1
    conn = sqlite3.connect(target / "wanderlens.sqlite3")
    subjects = {row[0] for row in conn.execute("SELECT subject FROM trip_subjects")}
    assert {"coastal", "mountains"} <= subjects
