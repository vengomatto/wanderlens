from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from PIL import Image

from wanderlens.catalog.fetch import (
    fetch_commons_category,
    fetch_commons_gallery,
    fetch_commons_imageinfo,
    fetch_wikidata_commons_category,
    fetch_wikidata_item_image,
    fetch_wikipedia_article_images,
    fetch_wikipedia_media,
    fetch_wikivoyage_page,
)
from wanderlens.catalog.regions import resolve_region
from wanderlens.core.models import Destination, DestinationMedia, MediaImage

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
GALLERY_LIMIT = 15
FALLBACK_MIN = 4
GOOD_MIMES = {"image/jpeg", "image/png", "image/webp"}
MIN_WIDTH = 800
BAD_TITLE_WORDS = (
    "icon",
    "logo",
    "map of",
    "locator",
    "location map",
    "flag",
    "coat of arms",
    "coat_of_arms",
    "diagram",
    "chart",
    "symbol",
    "banner",
    "emblem",
    "commons-logo",
    "wikimedia",
    "edit-",
    "disambig",
    "question book",
    "schematic",
)


ASSESSED_CATEGORIES = ("quality images", "featured pictures", "valued images")


def is_assessed(image: dict) -> bool:
    """Whether a Commons file belongs to a Quality / Featured / Valued set."""
    categories = (image.get("categories") or "").lower()
    return any(marker in categories for marker in ASSESSED_CATEGORIES)


def _dedupe_key(image: dict) -> str:
    title = (image.get("title") or "").strip().lower()
    if title:
        return title
    return (image.get("url") or "").rsplit("/", 1)[-1].lower()


def filter_images(images: list[dict], min_width: int = MIN_WIDTH, limit: int = GALLERY_LIMIT) -> list[dict]:
    """Keep usable photographs, best first.

    Drops non-photo mime types, low-resolution files, and blocklisted titles;
    deduplicates; then prefers assessed (Quality/Featured/Valued) images, then
    larger and landscape-oriented ones.
    """
    seen: set[str] = set()
    kept: list[dict] = []
    for image in images:
        title = (image.get("title") or "").lower()
        if image.get("mime") not in GOOD_MIMES:
            continue
        if int(image.get("width") or 0) < min_width:
            continue
        if any(word in title for word in BAD_TITLE_WORDS):
            continue
        key = _dedupe_key(image)
        if key in seen:
            continue
        seen.add(key)
        kept.append(image)

    kept.sort(
        key=lambda image: (
            not is_assessed(image),
            int(image.get("height") or 0) >= int(image.get("width") or 0),
            -int(image.get("width") or 0),
        )
    )
    return kept[:limit]


def _safe(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except Exception:
        return None


class OpenverseMediaProvider:
    """Additional openly-licensed images from the Openverse API (keyless).

    Used as an *additional* source alongside Wikimedia/Commons; its images are
    filtered and deduplicated like the rest, and a failure is ignored.
    """

    name = "openverse"
    API = "https://api.openverse.org/v1/images/"

    def __init__(self, session=None, timeout: int = 30, page_size: int = 20):
        self.session = session
        self.timeout = timeout
        self.page_size = page_size

    def images(self, destination: Destination) -> list[dict]:
        import requests

        from wanderlens.catalog.fetch import USER_AGENT

        query = f"{destination.name} {destination.country}".strip()
        response = (self.session or requests).get(
            self.API,
            params={"q": query, "page_size": self.page_size, "license_type": "commercial"},
            headers={"User-Agent": USER_AGENT},
            timeout=self.timeout,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        images: list[dict] = []
        for item in results:
            url = item.get("url")
            if not url:
                continue
            filetype = (item.get("filetype") or "jpg").lower()
            mime = "image/jpeg" if filetype in {"jpg", "jpeg"} else f"image/{filetype}"
            images.append(
                {
                    "title": item.get("title", ""),
                    "url": url,
                    "width": int(item.get("width") or 0),
                    "height": int(item.get("height") or 0),
                    "mime": mime,
                    "license": item.get("license", ""),
                    "attribution": item.get("creator", ""),
                    "source": "openverse",
                }
            )
        return images


class WikimediaMediaProvider:
    """Travel-oriented description (Wikivoyage) + Wikipedia hero + Commons gallery."""

    name = "wikimedia"

    def __init__(self, session=None, gallery_limit: int = GALLERY_LIMIT, extra_sources=None):
        self.session = session
        self.gallery_limit = gallery_limit
        self.extra_sources = extra_sources or []

    def fetch(self, destination: Destination) -> Optional[DestinationMedia]:
        voyage = _safe(
            fetch_wikivoyage_page, destination.name, destination.country, session=self.session
        )
        wiki = _safe(
            fetch_wikipedia_media, destination.name, destination.country, session=self.session
        )
        if not voyage and not wiki:
            return None

        extract = (voyage or {}).get("extract") or (wiki or {}).get("extract", "")
        page_url = (voyage or {}).get("page_url") or (wiki or {}).get("page_url", "")
        title = (wiki or {}).get("title") or (voyage or {}).get("title", "")
        wikidata_id = (voyage or {}).get("wikidata_id", "")

        hero: Optional[dict] = None
        curated: list[dict] = []
        if wikidata_id:
            item_images = _safe(fetch_wikidata_item_image, wikidata_id, session=self.session) or []
            if item_images:
                hero = item_images[0]
                curated.extend(item_images[1:])
        if hero is None and wiki and wiki.get("image_url"):
            hero = {
                "url": wiki["image_url"],
                "source": "wikipedia",
                "license": wiki.get("image_license", ""),
                "attribution": wiki.get("image_attribution", "Wikipedia"),
            }

        if title:
            files = _safe(fetch_wikipedia_article_images, title, session=self.session) or []
            curated.extend(_safe(fetch_commons_imageinfo, files, session=self.session) or [])
        category = (
            _safe(fetch_wikidata_commons_category, wikidata_id, session=self.session)
            if wikidata_id
            else None
        ) or destination.name
        curated.extend(_safe(fetch_commons_category, category, session=self.session) or [])

        for source in self.extra_sources:
            curated.extend(_safe(source.images, destination) or [])

        gallery = filter_images(curated)

        images: list[MediaImage] = []
        hero_url = hero["url"] if hero else None
        if hero:
            images.append(
                MediaImage(
                    url=hero_url,
                    source=hero.get("source", ""),
                    license=hero.get("license", ""),
                    attribution=hero.get("attribution", ""),
                )
            )
        for item in gallery:
            if item["url"] == hero_url:
                continue
            images.append(
                MediaImage(
                    url=item["url"],
                    source=item.get("source", "commons"),
                    license=item.get("license", ""),
                    attribution=item.get("attribution", ""),
                )
            )

        if len(images) < FALLBACK_MIN and destination.lat is not None and destination.lon is not None:
            nearby = _safe(
                fetch_commons_gallery,
                destination.lat,
                destination.lon,
                session=self.session,
                limit=self.gallery_limit,
            ) or []
            seen_urls = {image.url for image in images}
            for item in filter_images(nearby, limit=self.gallery_limit):
                if item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                images.append(
                    MediaImage(
                        url=item["url"],
                        source=item.get("source", "commons"),
                        license=item.get("license", ""),
                        attribution=item.get("attribution", ""),
                    )
                )

        return DestinationMedia(
            destination_id=destination.id,
            title=title,
            page_url=page_url,
            extract=extract,
            source=self.name,
            images=images,
        )


class CommonsMediaProvider:
    """Fallback: a Commons gallery only, when Wikipedia yields nothing."""

    name = "commons"

    def __init__(self, session=None, limit: int = GALLERY_LIMIT):
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


def build_media_chain(session=None, sources=None) -> list:
    extra = []
    for name in sources or []:
        if name == "openverse":
            extra.append(OpenverseMediaProvider(session=session))
    return [WikimediaMediaProvider(session=session, extra_sources=extra), CommonsMediaProvider(session=session)]


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


def _fetch_bytes(session, url: str) -> bytes:
    import requests

    from wanderlens.catalog.fetch import USER_AGENT

    http = session or requests
    response = http.get(url, headers={"User-Agent": USER_AGENT}, timeout=60)
    response.raise_for_status()
    return response.content


def _average_hash(data: bytes) -> int:
    """A 64-bit average hash for perceptual near-duplicate detection."""
    with Image.open(BytesIO(data)) as image:
        pixels = list(image.convert("L").resize((8, 8)).tobytes())
    average = sum(pixels) / len(pixels)
    bits = 0
    for index, value in enumerate(pixels):
        if value >= average:
            bits |= 1 << index
    return bits


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


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
    refresh: bool = False,
) -> bool:
    """Fetch and cache media for one destination. Returns whether it was fetched."""
    if is_media_cached(conn, destination.id) and not refresh:
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
    kept_hashes: list[int] = []
    for image in bundle.images if bundle else []:
        try:
            data = _fetch_bytes(session, image.url)
        except Exception:
            continue
        try:
            digest = _average_hash(data)
        except Exception:
            digest = None
        if digest is not None and any(
            other is not None and _hamming(digest, other) <= 4 for other in kept_hashes
        ):
            continue
        kept_hashes.append(digest)
        filename = f"{key}_{len(downloaded)}{_extension(image.url)}"
        try:
            (media_dir / filename).write_bytes(data)
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
    refresh: bool = False,
) -> int:
    """Best-effort media fetch for a batch of recommendations; never raises."""
    stored = 0
    for rec in recommendations:
        try:
            if fetch_media(
                conn, rec.destination, media_dir, chain=chain, session=session, refresh=refresh
            ):
                stored += 1
        except Exception:
            continue
    return stored
