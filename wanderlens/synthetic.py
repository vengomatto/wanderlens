from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

from wanderlens.catalog.destinations import destination_to_dict
from wanderlens.core.models import Destination

# Several taste clusters so the catalog is broad and ranking has variety.
_CLUSTERS: dict[str, dict] = {
    "coastal": {"lat": 40.0, "lon": 14.0, "color": (40, 110, 180), "attributes": ["coastal", "beach", "water", "boats"]},
    "mountain": {"lat": 46.4, "lon": 11.7, "color": (70, 110, 60), "attributes": ["mountains", "hiking", "nature", "snow"]},
    "city": {"lat": 41.9, "lon": 12.5, "color": (150, 120, 90), "attributes": ["city", "architecture", "museum", "food"]},
    "countryside": {"lat": 43.0, "lon": 11.0, "color": (120, 150, 80), "attributes": ["countryside", "village", "food", "nature"]},
    "lake": {"lat": 45.5, "lon": 9.5, "color": (60, 140, 160), "attributes": ["lake", "nature", "boats", "mountains"]},
    "desert": {"lat": 37.0, "lon": -3.0, "color": (200, 170, 110), "attributes": ["desert", "sunset", "nature", "history"]},
}
_CLUSTER_ORDER = list(_CLUSTERS)
_ATTRIBUTES = {name: spec["attributes"] for name, spec in _CLUSTERS.items()}
_CLUSTER_VECTORS = {
    name: np.eye(len(_CLUSTER_ORDER), dtype=np.float32)[index]
    for index, name in enumerate(_CLUSTER_ORDER)
}
_KEYWORDS = {
    "coastal": ("coast", "beach", "water", "boat", "sea"),
    "mountain": ("mountain", "hiking", "snow", "peak"),
    "city": ("city", "urban", "architecture", "museum"),
    "countryside": ("countryside", "village", "rural", "farm"),
    "lake": ("lake", "fjord", "reservoir"),
    "desert": ("desert", "dune"),
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
    trips_per_taste: int = 10,
    destinations_per_taste: int = 50,
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

    for cluster_index, cluster in enumerate(_CLUSTER_ORDER):
        spec = _CLUSTERS[cluster]
        other = _CLUSTER_ORDER[(cluster_index + 1) % len(_CLUSTER_ORDER)]
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
            attributes = _ATTRIBUTES[cluster] if match else _ATTRIBUTES[other]
            destinations.append(
                Destination(
                    id=f"syn:{cluster}:{dest_index:03d}",
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


class SyntheticVision:
    """A deterministic stand-in for the vision model: tags from the photo's cluster."""

    def describe(self, paths) -> list[str]:
        attributes: list[str] = []
        for path in paths:
            cluster = Path(path).name.split("_")[0]
            attributes.extend(_ATTRIBUTES.get(cluster, []))
        return attributes


class SyntheticEmbedder:
    """A deterministic cluster-based embedder, so no ONNX runtime is needed."""

    dim = len(_CLUSTER_ORDER)

    def _cluster(self, path: str) -> str:
        return Path(path).name.split("_")[0]

    def embed_image(self, path: str):
        return _CLUSTER_VECTORS.get(self._cluster(path), np.zeros(self.dim, dtype=np.float32))

    def embed_text(self, text: str):
        lowered = (text or "").lower()
        for cluster in _CLUSTER_ORDER:
            if cluster in lowered:
                return _CLUSTER_VECTORS[cluster]
            if any(word in lowered for word in _KEYWORDS[cluster]):
                return _CLUSTER_VECTORS[cluster]
        return np.zeros(self.dim, dtype=np.float32)


def seed_profile(target_dir: str | Path) -> int:
    """Ingest and profile the materialised archive with the synthetic vision/embedder."""
    from wanderlens.config import Config
    from wanderlens.pipeline.ingest import run_ingest
    from wanderlens.pipeline.profile import run_profile

    target = Path(target_dir)
    config = Config(
        data_dir=target,
        photos_dir=target / "photos",
        db_path=target / "wanderlens.sqlite3",
        catalog_path=target / "catalog",
        vlm_provider="synthetic",
        vlm_model="synthetic",
        api_key=None,
    )
    run_ingest(config)
    trips = run_profile(config, embedder=SyntheticEmbedder(), vision=SyntheticVision())
    return len(trips)
