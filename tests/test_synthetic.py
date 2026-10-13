from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.sources.folder import FolderSource
from wanderlens.synthetic import materialize


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
