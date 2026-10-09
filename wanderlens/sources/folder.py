from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image
from PIL.ExifTags import GPSTAGS

from wanderlens.core.models import Photo

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic"}

_TAG_DATETIME_ORIGINAL = 36867
_TAG_DATETIME = 306
_TAG_GPS_IFD = 0x8825


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _to_degrees(value) -> float:
    d, m, s = (float(x) for x in value)
    return d + m / 60.0 + s / 3600.0


def extract_gps(exif) -> Optional[tuple[float, float]]:
    ifd = exif.get_ifd(_TAG_GPS_IFD)
    if not ifd:
        return None
    gps = {GPSTAGS.get(k, k): v for k, v in ifd.items()}
    lat, lon = gps.get("GPSLatitude"), gps.get("GPSLongitude")
    if not (lat and lon):
        return None
    lat_d = _to_degrees(lat)
    lon_d = _to_degrees(lon)
    if gps.get("GPSLatitudeRef") == "S":
        lat_d = -lat_d
    if gps.get("GPSLongitudeRef") == "W":
        lon_d = -lon_d
    return lat_d, lon_d


def extract_taken_at(exif) -> Optional[datetime]:
    raw = exif.get(_TAG_DATETIME_ORIGINAL) or exif.get(_TAG_DATETIME)
    if not raw:
        exif_ifd = exif.get_ifd(0x8769)
        if exif_ifd:
            raw = exif_ifd.get(_TAG_DATETIME_ORIGINAL)
    if not raw:
        return None
    try:
        return datetime.strptime(str(raw).strip(), "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None


class FolderSource:
    """Reads a Photo Archive from a directory tree of image files."""

    name = "folder"

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def iter_photos(self):
        if not self.root.exists():
            return
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                yield self._to_photo(path)

    def _to_photo(self, path: Path) -> Photo:
        sha = sha256_of(path)
        taken_at: Optional[datetime] = None
        lat = lon = None
        width = height = None
        try:
            with Image.open(path) as image:
                width, height = image.size
                exif = image.getexif()
                taken_at = extract_taken_at(exif)
                location = extract_gps(exif)
                if location:
                    lat, lon = location
        except Exception:
            pass
        return Photo(
            id=f"{self.name}:{sha}",
            source=self.name,
            path=str(path),
            sha256=sha,
            taken_at=taken_at,
            lat=lat,
            lon=lon,
            width=width,
            height=height,
        )
