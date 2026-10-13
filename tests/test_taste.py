from datetime import datetime, timedelta

from wanderlens.core.models import Photo
from wanderlens.core.taste import cluster_into_trips, geography_weights, to_trips


def _photo(idx, when, lat=None, lon=None):
    return Photo(
        id=str(idx), source="t", path=f"/p/{idx}.jpg", sha256=str(idx),
        taken_at=when, lat=lat, lon=lon,
    )


def test_same_trip_groups_nearby_in_time():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [
        _photo(1, base, 44.18, 9.58),
        _photo(2, base + timedelta(minutes=5), 44.19, 9.59),
        _photo(3, base + timedelta(hours=1), 44.20, 9.60),
    ]
    clusters = cluster_into_trips(photos)
    assert len(clusters) == 1


def test_time_gap_splits_trips():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [
        _photo(1, base),
        _photo(2, base + timedelta(days=2)),
    ]
    clusters = cluster_into_trips(photos)
    assert len(clusters) == 2


def test_spatial_jump_splits_trips():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [
        _photo(1, base, 44.18, 9.58),
        _photo(2, base + timedelta(hours=1), 35.90, 14.51),
    ]
    clusters = cluster_into_trips(photos)
    assert len(clusters) == 2


def test_to_trips_labels_with_reverse_geocoder():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [_photo(1, base, 44.18, 9.58)]
    trips = to_trips(cluster_into_trips(photos), reverse_geocoder=lambda lat, lon: ("Levanto", "Italy"))
    assert trips[0].country == "Italy"
    assert trips[0].city == "Levanto"


def test_geography_weights_normalized():
    base = datetime(2025, 12, 29, 10, 0, 0)
    p = [_photo(1, base, 44.18, 9.58)]
    trips = to_trips(cluster_into_trips(p), reverse_geocoder=lambda lat, lon: ("Levanto", "Italy"))
    weights = geography_weights(trips)
    assert weights == {"Italy": 1.0}


def test_default_split_thresholds_unchanged():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [_photo(1, base), _photo(2, base + timedelta(hours=24))]
    assert len(cluster_into_trips(photos)) == 2, "default 18h gap splits"


def test_configurable_split_window_merges():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [_photo(1, base), _photo(2, base + timedelta(hours=24))]
    merged = cluster_into_trips(photos, max_gap=timedelta(hours=48))
    assert len(merged) == 1


def test_configurable_spatial_jump():
    base = datetime(2025, 12, 29, 10, 0, 0)
    photos = [_photo(1, base, 44.18, 9.58), _photo(2, base + timedelta(hours=1), 35.90, 14.51)]
    assert len(cluster_into_trips(photos, max_jump_km=2000)) == 1

