from pathlib import Path

import piexif
from PIL import Image

from wanderlens.config import Config
from wanderlens.core.models import Photo
from wanderlens.pipeline.ingest import run_ingest
from wanderlens.sources.folder import FolderSource


def _make_config(tmp_path: Path) -> Config:
    return Config(
        data_dir=tmp_path,
        photos_dir=tmp_path / "photos",
        db_path=tmp_path / "wl.sqlite3",
        catalog_path=tmp_path / "catalog",
        vlm_provider="test",
        vlm_model="test",
        api_key=None,
    )


def _write_image(path: Path, *, gps: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (320, 240), (10, 120, 200))
    exif_bytes = None
    if gps:
        exif = {
            "0th": {},
            "Exif": {piexif.ExifIFD.DateTimeOriginal: b"2025:12:29 13:53:00"},
            "GPS": {
                piexif.GPSIFD.GPSLatitudeRef: b"N",
                piexif.GPSIFD.GPSLatitude: ((44, 1), (10, 1), (5995, 100)),
                piexif.GPSIFD.GPSLongitudeRef: b"E",
                piexif.GPSIFD.GPSLongitude: ((9, 1), (34, 1), (4917, 100)),
            },
            "1st": {},
            "thumbnail": None,
        }
        exif_bytes = piexif.dump(exif)
    if exif_bytes is not None:
        image.save(path, exif=exif_bytes)
    else:
        image.save(path)


def test_folder_source_lists_only_images(tmp_path):
    _write_image(tmp_path / "a.jpg")
    _write_image(tmp_path / "b.jpeg")
    (tmp_path / "notes.txt").write_text("not an image")

    photos = list(FolderSource(tmp_path).iter_photos())

    assert {Path(p.path).name for p in photos} == {"a.jpg", "b.jpeg"}


def test_extracts_gps_and_dimensions(tmp_path):
    with_gps = tmp_path / "with.jpg"
    without = tmp_path / "without.jpg"
    _write_image(with_gps, gps=True)
    _write_image(without, gps=False)

    by_name = {Path(p.path).name: p for p in FolderSource(tmp_path).iter_photos()}

    gps_photo = by_name["with.jpg"]
    assert gps_photo.lat == 44.1833 or abs(gps_photo.lat - 44.18332) < 1e-3
    assert abs(gps_photo.lon - 9.58033) < 1e-3
    assert gps_photo.width == 320 and gps_photo.height == 240

    no_gps = by_name["without.jpg"]
    assert no_gps.lat is None and no_gps.lon is None
    assert no_gps.width == 320


class _FakeSource:
    name = "fake"

    def __init__(self, photos):
        self._photos = photos

    def iter_photos(self):
        return iter(self._photos)


def _fake_photo(idx: int) -> Photo:
    return Photo(id=f"fake:{idx}", source="fake", path=f"/x/{idx}.jpg", sha256=f"sha{idx}")


def test_ingest_from_fake_source(tmp_path):
    config = _make_config(tmp_path)
    added = run_ingest(config, source=_FakeSource([_fake_photo(1), _fake_photo(2)]))
    assert added == 2


def test_ingest_is_idempotent(tmp_path):
    _write_image(tmp_path / "photos" / "a.jpg", gps=True)
    config = _make_config(tmp_path)

    assert run_ingest(config) == 1
    assert run_ingest(config) == 0
