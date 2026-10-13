from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from PIL import Image

from wanderlens.catalog.destinations import destination_to_dict
from wanderlens.core.models import Destination

# Two taste clusters so ranking has something to separate.
_CLUSTERS = {
    "coastal": {"lat": 40.0, "lon": 14.0, "color": (40, 110, 180)},
    "mountain": {"lat": 46.4, "lon": 11.7, "color": (70, 110, 60)},
}
_ATTRIBUTES = {
    "coastal": ["coastal", "beach", "water", "boats"],
    "mountain": ["mountains", "hiking", "nature", "snow"],
}


def _gps_degrees(value: float) -> tuple:
    degrees = int(abs(value))
    minutes_float = (abs(value) - degrees) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60 * 100)
    return ((degrees, 1), (minutes, 1), (seconds, 100))


def _write_photo(path: Path, cluster: str, index: int, taken_at: datetime, lat: float, lon: float) -> None:
    import piexif

    base = _CLUSTERS[cluster]["color"]
    shift = (index * 17) % 90
    color = tuple(min(255, c + shift) for c in base)
    Image.new("RGB", (640, 480), color).save(path)

    exif = {
        "0th": {},
        "Exif": {piexif.ExifIFD.DateTimeOriginal: taken_at.strftime("%Y:%m:%d %H:%M:%S").encode()},
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: (b"N" if lat >= 0 else b"S"),
            piexif.GPSIFD.GPSLatitude: _gps_degrees(lat),
            piexif.GPSIFD.GPSLongitudeRef: (b"E" if lon >= 0 else b"W"),
            piexif.GPSIFD.GPSLongitude: _gps_degrees(lon),
        },
        "1st": {},
        "thumbnail": None,
    }
    piexif.insert(piexif.dump(exif), str(path))


def materialize(
    target_dir: str | Path,
    trips_per_taste: int = 8,
    destinations_per_taste: int = 12,
    photos_per_trip: int = 6,
    seed: int = 0,
) -> dict:
    """Write a deterministic mock photo archive and candidate catalog.

    Returns counts; the archive is meant to be run through the normal pipeline by
    pointing ``WANDERLENS_DATA_DIR`` at ``target_dir``.
    """
    target = Path(target_dir)
    photos_dir = target / "photos"
    catalog_dir = target / "catalog"
    photos_dir.mkdir(parents=True, exist_ok=True)
    catalog_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    destinations: list[Destination] = []
    photo_count = 0
    trip_count = 0
    base_date = datetime(2024, 5, 1, 9, 0, 0)
    trip_serial = 0

    for cluster, spec in _CLUSTERS.items():
        for trip_index in range(trips_per_taste):
            trip_count += 1
            lat0 = spec["lat"] + rng.uniform(-0.4, 0.4)
            lon0 = spec["lon"] + rng.uniform(-0.4, 0.4)
            start = base_date + timedelta(days=trip_serial * 20)
            trip_serial += 1
            for photo_index in range(photos_per_trip):
                lat = lat0 + rng.uniform(-0.02, 0.02)
                lon = lon0 + rng.uniform(-0.02, 0.02)
                taken = start + timedelta(hours=photo_index * 2)
                name = f"{cluster}_{trip_index:02d}_{photo_index:02d}.jpg"
                _write_photo(photos_dir / name, cluster, photo_index, taken, lat, lon)
                photo_count += 1

        for dest_index in range(destinations_per_taste):
            match = dest_index < destinations_per_taste // 3
            attributes = _ATTRIBUTES[cluster] if match else _ATTRIBUTES[
                "mountain" if cluster == "coastal" else "coastal"
            ]
            destinations.append(
                Destination(
                    id=f"syn:{cluster}:{dest_index:02d}",
                    name=f"{cluster.title()} Place {dest_index}",
                    lat=spec["lat"] + rng.uniform(-1.5, 1.5),
                    lon=spec["lon"] + rng.uniform(-1.5, 1.5),
                    country="Synthetic",
                    attributes=list(attributes),
                    description=f"A {cluster} destination in the synthetic catalog.",
                )
            )

    (catalog_dir / "destinations.json").write_text(
        json.dumps([destination_to_dict(d) for d in destinations], indent=2)
    )
    return {"photos": photo_count, "trips": trip_count, "destinations": len(destinations)}
