from pathlib import Path

import numpy as np
import piexif
from PIL import Image

from wanderlens.config import Config
from wanderlens.pipeline.ingest import run_ingest
from wanderlens.pipeline.profile import run_profile, show_profile


class FakeEmbedder:
    dim = 4

    def embed_image(self, path):
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    def embed_text(self, text):
        return np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32)


class FakeVision:
    def __init__(self, tags):
        self.tags = tags
        self.calls = 0

    def describe(self, paths):
        self.calls += 1
        return list(self.tags)


def _config(tmp_path):
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=tmp_path / "catalog",
        vlm_provider="test",
        vlm_model="test",
        api_key=None,
    )


def _write(path, taken):
    path.parent.mkdir(parents=True, exist_ok=True)
    exif = {
        "0th": {},
        "Exif": {piexif.ExifIFD.DateTimeOriginal: taken.encode()},
        "1st": {},
        "GPS": {
            piexif.GPSIFD.GPSLatitudeRef: b"N",
            piexif.GPSIFD.GPSLatitude: ((44, 1), (10, 1), (5995, 100)),
            piexif.GPSIFD.GPSLongitudeRef: b"E",
            piexif.GPSIFD.GPSLongitude: ((9, 1), (34, 1), (4917, 100)),
        },
        "thumbnail": None,
    }
    Image.new("RGB", (64, 64), (20, 20, 20)).save(path, exif=piexif.dump(exif))


def _italy(lat, lon):
    return ("Levanto", "Italy")


def _seed(config):
    _write(config.photos_dir / "a.jpg", "2025:12:29 13:00:00")
    _write(config.photos_dir / "b.jpg", "2025:12:29 14:00:00")
    _write(config.photos_dir / "c.jpg", "2026:01:05 09:00:00")
    run_ingest(config)


def test_run_profile_stores_factors_and_embeddings(tmp_path):
    config = _config(tmp_path)
    _seed(config)
    vision = FakeVision(["coastal cliffs", "hiking"])

    trips = run_profile(
        config,
        embedder=FakeEmbedder(),
        vision=vision,
        reverse_geocoder=_italy,
    )

    assert len(trips) == 2
    assert vision.calls == 2

    import sqlite3

    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    entries = {(r["factor"], r["key"]): r["value"] for r in conn.execute("SELECT * FROM profile_entries")}
    assert entries[("geography", "Italy")] == 1.0
    assert ("subjects", "coastal") in entries
    assert conn.execute("SELECT COUNT(*) FROM photo_embeddings").fetchone()[0] == 3


def test_attributes_weighted_by_trip_recurrence(tmp_path):
    config = _config(tmp_path)
    _seed(config)  # two trips: a,b (one trip) and c (another)

    class PerTripVision:
        def __init__(self):
            self.n = 0

        def describe(self, paths):
            self.n += 1
            return ["coastal cliffs"] if self.n == 1 else ["mountains"]

    run_profile(config, embedder=FakeEmbedder(), vision=PerTripVision(), reverse_geocoder=_italy)

    import sqlite3

    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    entries = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM profile_entries WHERE factor='subjects'")}
    # coastal appears in trip 1 only (1/2); mountains in trip 2 only (1/2)
    assert entries["coastal"] == 0.5
    assert entries["mountains"] == 0.5


def test_subjects_require_vision_optin(tmp_path):
    config = _config(tmp_path)
    _seed(config)

    run_profile(config, embedder=FakeEmbedder(), vision=None, reverse_geocoder=_italy)

    import sqlite3

    conn = sqlite3.connect(config.db_path)
    subjects = conn.execute("SELECT COUNT(*) FROM profile_entries WHERE factor='subjects'").fetchone()[0]
    assert subjects == 0


def test_show_profile_reports_factors(tmp_path):
    config = _config(tmp_path)
    _seed(config)
    run_profile(
        config,
        embedder=FakeEmbedder(),
        vision=FakeVision(["coastal cliffs"]),
        reverse_geocoder=_italy,
    )

    text = show_profile(config)

    assert "Italy" in text
    assert "coastal" in text
    assert "Trips: 2" in text


def test_tagging_is_idempotent(tmp_path):
    config = _config(tmp_path)
    _seed(config)
    vision = FakeVision(["coastal cliffs"])

    run_profile(config, embedder=FakeEmbedder(), vision=vision, reverse_geocoder=_italy)
    calls = vision.calls
    assert calls > 0

    run_profile(config, embedder=FakeEmbedder(), vision=vision, reverse_geocoder=_italy)
    assert vision.calls == calls, "tagging should be cached and not re-sent"

    run_profile(config, embedder=FakeEmbedder(), vision=vision, reverse_geocoder=_italy, retag=True)
    assert vision.calls > calls
