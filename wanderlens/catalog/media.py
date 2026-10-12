from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from wanderlens.catalog.fetch import fetch_commons_gallery, fetch_wikipedia_media
from wanderlens.catalog.regions import resolve_region
from wanderlens.core.models import Destination, DestinationMedia, MediaImage

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


class WikimediaMediaProvider:
    """Wikipedia hero image + expanded extract, plus a Commons gallery nearby."""

    name = "wikimedia"

    def __init__(self, session=None):
        self.session = session

    def fetch(self, destination: Destination) -> Optional[DestinationMedia]:
        try:
            data = fetch_wikipedia_media(
                destination.name, destination.country, session=self.session
            )
        except Exception:
            data = None
        if not data:
            return None

        media = DestinationMedia(
            destination_id=destination.id,
            title=data.get("title", ""),
            page_url=data.get("page_url", ""),
            extract=data.get("extract", ""),
            source=self.name,
        )
        if data.get("image_url"):
            media.images.append(
                MediaImage(
                    url=data["image_url"],
                    source="wikipedia",
                    license=data.get("image_license", ""),
                    attribution=data.get("image_attribution", ""),
                )
            )
        if destination.lat is not None and destination.lon is not None:
            try:
                gallery = fetch_commons_gallery(
                    destination.lat, destination.lon, session=self.session
                )
            except Exception:
                gallery = []
            media.images.extend(MediaImage(**item) for item in gallery)
        return media


class CommonsMediaProvider:
    """Fallback: a Commons gallery only, when Wikipedia yields nothing."""

    name = "commons"

    def __init__(self, session=None, limit: int = 4):
        self.session = session
        self.limit = limit

    def fetch(self, destination: Destination) -> Optional[DestinationMedia]:
        if destination.lat is None or destination.lon is None:
            return None
        try:
            gallery = fetch_commons_gallery(
                destination.lat, destination.lon, session=self.session, limit=self.limit
            )
        except Exception:
            gallery = []
        if not gallery:
            return None
        return DestinationMedia(
            destination_id=destination.id,
            source=self.name,
            images=[MediaImage(**item) for item in gallery],
        )


def build_media_chain(session=None) -> list:
    return [WikimediaMediaProvider(session=session), CommonsMediaProvider(session=session)]


def _safe_id(destination_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", destination_id)


def _extension(url: str) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in IMAGE_EXTENSIONS else ".jpg"


def _download(session, url: str, destination: Path) -> None:
    import requests

    from wanderlens.catalog.fetch import USER_AGENT

    http = session or requests
    response = http.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)


def is_media_cached(conn: sqlite3.Connection, destination_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM destination_media WHERE destination_id = ?", (destination_id,)
    ).fetchone()
    return row is not None


def fetch_media(
    conn: sqlite3.Connection,
    destination: Destination,
    media_dir: str | Path,
    chain: Optional[list] = None,
    session=None,
) -> bool:
    """Fetch and cache media for one destination. Returns whether it was fetched."""
    if is_media_cached(conn, destination.id):
        return False

    chain = chain if chain is not None else build_media_chain(session=session)
    bundle: Optional[DestinationMedia] = None
    for provider in chain:
        try:
            candidate = provider.fetch(destination)
        except Exception:
            candidate = None
        if candidate is not None and (candidate.images or candidate.extract):
            bundle = candidate
            break

    try:
        geojson, kind, radius = resolve_region(destination, session=session)
    except Exception:
        geojson, kind, radius = "", "", None

    media_dir = Path(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    key = _safe_id(destination.id)

    downloaded: list[tuple[str, str, str, str]] = []
    for image in bundle.images if bundle else []:
        filename = f"{key}_{len(downloaded)}{_extension(image.url)}"
        try:
            _download(session, image.url, media_dir / filename)
        except Exception:
            continue
        downloaded.append((filename, image.source, image.license, image.attribution))

    conn.execute(
        "INSERT OR REPLACE INTO destination_media "
        "(destination_id, title, page_url, extract, source, license, attribution, "
        " region_geojson, region_kind, region_radius_km, fetched_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            destination.id,
            bundle.title if bundle else "",
            bundle.page_url if bundle else "",
            bundle.extract if bundle else "",
            bundle.source if bundle else "",
            bundle.license if bundle else "",
            bundle.attribution if bundle else "",
            geojson,
            kind,
            radius,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.execute("DELETE FROM destination_images WHERE destination_id = ?", (destination.id,))
    for position, (filename, source, license_, attribution) in enumerate(downloaded):
        conn.execute(
            "INSERT INTO destination_images "
            "(destination_id, position, filename, source, license, attribution) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (destination.id, position, filename, source, license_, attribution),
        )
    conn.commit()
    return True


def fetch_media_for(
    conn: sqlite3.Connection,
    recommendations,
    media_dir: str | Path,
    chain: Optional[list] = None,
    session=None,
) -> int:
    """Best-effort media fetch for a batch of recommendations; never raises."""
    stored = 0
    for rec in recommendations:
        try:
            if fetch_media(conn, rec.destination, media_dir, chain=chain, session=session):
                stored += 1
        except Exception:
            continue
    return stored
