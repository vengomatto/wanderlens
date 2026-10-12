from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog, normalize_record

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "wanderlens/0.1 (personal project; noreply@users.noreply.github.com)"


def fetch_wikipedia_summary(
    name: str, country: str = "", session=None, timeout: int = 30
) -> str:
    """First-sentence Wikipedia intro for a place, via country-qualified search."""
    import requests

    session = session or requests
    response = session.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{name} {country}".strip(),
            "gsrlimit": 1,
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return ""
    page = next(iter(pages.values()))
    extract = " ".join(page.get("extract", "").split())
    return extract[:300]


def _strip_html(value: str) -> str:
    import re

    return " ".join(re.sub(r"<[^>]+>", " ", value or "").split())


def _meta(metadata: dict, key: str) -> str:
    entry = metadata.get(key) or {}
    return str(entry.get("value", "")) if isinstance(entry, dict) else ""


def fetch_wikipedia_media(
    name: str, country: str = "", session=None, timeout: int = 30, max_chars: int = 1500
) -> Optional[dict]:
    """Hero image + expanded extract + source link for a place, from Wikipedia."""
    import requests

    session = session or requests
    response = session.get(
        WIKIPEDIA_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"{name} {country}".strip(),
            "gsrlimit": 1,
            "prop": "extracts|pageimages|info",
            "explaintext": 1,
            "exlimit": 1,
            "piprop": "thumbnail",
            "pithumbsize": 1280,
            "inprop": "url",
            "redirects": 1,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    if not pages:
        return None
    page = next(iter(pages.values()))
    extract = " ".join(page.get("extract", "").split())
    if len(extract) > max_chars:
        extract = extract[:max_chars].rsplit(" ", 1)[0]
    thumbnail = (page.get("thumbnail") or {}).get("source", "")
    if not extract and not thumbnail:
        return None
    return {
        "title": page.get("title", ""),
        "page_url": page.get("fullurl", ""),
        "extract": extract,
        "image_url": thumbnail,
        "image_license": "",
        "image_attribution": "Wikipedia",
    }


def fetch_commons_gallery(
    lat: float,
    lon: float,
    session=None,
    limit: int = 4,
    radius: int = 10000,
    timeout: int = 30,
    thumb_width: int = 1280,
) -> list[dict]:
    """A small gallery of Commons images geotagged near the coordinates."""
    import requests

    session = session or requests
    response = session.get(
        COMMONS_API,
        params={
            "action": "query",
            "format": "json",
            "generator": "geosearch",
            "ggscoord": f"{lat}|{lon}",
            "ggsradius": radius,
            "ggslimit": limit,
            "ggsnamespace": 6,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": thumb_width,
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    images: list[dict] = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        metadata = info.get("extmetadata") or {}
        images.append(
            {
                "url": url,
                "source": "commons",
                "license": _strip_html(_meta(metadata, "LicenseShortName")),
                "attribution": _strip_html(_meta(metadata, "Artist")),
            }
        )
    return images


def fetch_wikidata_description(name: str, session=None, timeout: int = 30) -> str:
    """Concise Wikidata description for a place."""
    import requests

    session = session or requests
    response = session.get(
        WIKIDATA_API,
        params={
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1,
            "type": "item",
        },
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    results = response.json().get("search", [])
    return results[0].get("description", "") if results else ""


def enrich_records(records: list[dict], providers=None, delay: float = 0.0) -> list[dict]:
    """Attach a description to each record via a provider chain; never fail the batch.

    Providers are tried in order; the first non-empty description wins.
    """
    import time

    from wanderlens.catalog.providers import WikimediaProvider

    if providers is None:
        providers = [WikimediaProvider()]

    for record in records:
        if record.get("description"):
            continue
        description = ""
        for provider in providers:
            try:
                description = provider.describe(record.get("name", ""), record.get("countryName", "")) or ""
            except Exception:
                description = ""
            if description:
                break
        record["description"] = description
        if delay:
            time.sleep(delay)
    return records


def country_names_for_codes(countries_path: str | Path, codes) -> dict[str, str]:
    """Map GeoNames country codes (e.g. 'ES') to country names ('Spain')."""
    wanted = {code.upper() for code in codes}
    result: dict[str, str] = {}
    path = Path(countries_path)
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5 and cols[0].upper() in wanted:
            result[cols[0].upper()] = cols[4]
    return result


def country_code_for_name(countries_path: str | Path, name: str) -> Optional[str]:
    """Map a country name (e.g. 'Malta') to its GeoNames code ('MT')."""
    path = Path(countries_path)
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if len(cols) >= 5 and cols[4].lower() == name.lower():
            return cols[0]
    return None


def load_geonames_cities(
    cities_path: str | Path,
    country_codes: Optional[Iterable[str]] = None,
    min_population: int = 0,
    limit: Optional[int] = None,
    countries_path: Optional[str | Path] = None,
) -> list[dict]:
    """Turn a GeoNames ``cities*.txt`` dump into raw Destination records."""
    codes = {c.upper() for c in country_codes} if country_codes else None
    country_names: dict[str, str] = {}
    if countries_path and Path(countries_path).exists():
        for line in Path(countries_path).read_text(encoding="utf-8", errors="replace").splitlines():
            if line and not line.startswith("#"):
                cols = line.split("\t")
                if len(cols) >= 5:
                    country_names[cols[0]] = cols[4]

    records: list[dict] = []
    for line in Path(cities_path).read_text(encoding="utf-8", errors="replace").splitlines():
        cols = line.split("\t")
        if len(cols) < 15:
            continue
        try:
            code = cols[8].upper()
            population = int(cols[14] or 0)
        except ValueError:
            continue
        if codes and code not in codes:
            continue
        if population < min_population:
            continue
        records.append(
            {
                "geonameId": cols[0],
                "name": cols[1],
                "latitude": float(cols[4]),
                "longitude": float(cols[5]),
                "countryName": country_names.get(code, code),
                "tags": [],
                "description": "",
            }
        )
        if limit and len(records) >= limit:
            break
    return records


def fetch_wikidata_candidates(query: str, timeout: int = 60) -> list[dict]:
    """Fetch Destination records from the Wikidata SPARQL endpoint."""
    import requests

    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"Accept": "application/sparql-results+json", "User-Agent": "wanderlens/0.1"},
        timeout=timeout,
    )
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    records = []
    for row in bindings:
        try:
            records.append(
                {
                    "id": row["item"]["value"].rsplit("/", 1)[-1],
                    "label": row["itemLabel"]["value"],
                    "lat": float(row["lat"]["value"]),
                    "lon": float(row["lon"]["value"]),
                    "country": row.get("countryLabel", {}).get("value", ""),
                    "tags": [],
                    "description": row.get("itemDescription", {}).get("value", ""),
                }
            )
        except (KeyError, ValueError):
            continue
    return records


def build_catalog(records: dict[str, list[dict]]) -> JsonCatalog:
    destinations = []
    for source, items in records.items():
        for raw in items:
            destinations.append(normalize_record(source, raw))
    return JsonCatalog(destinations)
