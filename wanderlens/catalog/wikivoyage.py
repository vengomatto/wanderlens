from __future__ import annotations

import re
import time
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.core.models import Destination

API = "https://en.wikivoyage.org/w/api.php"
USER_AGENT = "wanderlens/0.1 (personal project; noreply@users.noreply.github.com)"

_SECTIONS = (("Regions", "region"), ("Cities", "city"), ("Other destinations", "other"))
_SKIP_PREFIXES = ("file:", "image:", "category:")


def _section_links(wikitext: str, section: str) -> list[str]:
    match = re.search(
        rf"==+\s*{re.escape(section)}\s*==+(.*?)(?=\n==[^=]|\Z)", wikitext, re.S | re.I
    )
    if not match:
        return []
    titles = []
    for link in re.findall(r"\[\[([^\]|#]+)", match.group(1)):
        title = link.strip()
        if not title or title.lower().startswith(_SKIP_PREFIXES):
            continue
        titles.append(title)
    return titles


def country_destination_titles(wikitext: str) -> list[tuple[str, str]]:
    """Return (title, granularity) pairs from a country page's sections."""
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for section, granularity in _SECTIONS:
        for title in _section_links(wikitext, section):
            if title in seen:
                continue
            seen.add(title)
            pairs.append((title, granularity))
    return pairs


def _fetch_wikitext(page: str, session=None, timeout: int = 30) -> str:
    import requests

    session = session or requests
    response = session.get(
        API,
        params={"action": "parse", "page": page, "prop": "wikitext", "format": "json", "redirects": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["parse"]["wikitext"]["*"]


def _fetch_pages(titles: list[str], session=None, timeout: int = 30, batch: int = 20) -> list[dict]:
    import requests

    session = session or requests
    pages: list[dict] = []
    for start in range(0, len(titles), batch):
        chunk = titles[start : start + batch]
        response = session.get(
            API,
            params={
                "action": "query",
                "titles": "|".join(chunk),
                "prop": "coordinates|extracts",
                "exintro": 1,
                "explaintext": 1,
                "redirects": 1,
                "format": "json",
            },
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
        response.raise_for_status()
        pages.extend(response.json().get("query", {}).get("pages", {}).values())
    return pages


def build_country_destinations(country: str, session=None, timeout: int = 30) -> list[Destination]:
    wikitext = _fetch_wikitext(country, session=session, timeout=timeout)
    pairs = country_destination_titles(wikitext)
    if not pairs:
        return []
    granularity = {title: gran for title, gran in pairs}
    destinations: list[Destination] = []
    for page in _fetch_pages([title for title, _ in pairs], session=session, timeout=timeout):
        coordinates = page.get("coordinates") or []
        if not coordinates:
            continue
        title = page["title"]
        gran = granularity.get(title) or granularity.get(title.split(" (")[0]) or "other"
        extract = " ".join((page.get("extract") or "").split())[:300]
        destinations.append(
            Destination(
                id=f"wv:{title}",
                name=title,
                lat=float(coordinates[0]["lat"]),
                lon=float(coordinates[0]["lon"]),
                country=country,
                description=extract,
                granularity=gran,
            )
        )
    return destinations


def build_wikivoyage_catalog(countries: Iterable[str], session=None, timeout: int = 30) -> JsonCatalog:
    destinations: list[Destination] = []
    for country in countries:
        try:
            destinations.extend(build_country_destinations(country, session=session, timeout=timeout))
        except Exception:
            continue
    return JsonCatalog(destinations)
