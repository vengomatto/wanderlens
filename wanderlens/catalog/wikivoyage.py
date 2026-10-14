from __future__ import annotations

import re
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog
from wanderlens.core.models import Destination

API = "https://en.wikivoyage.org/w/api.php"
USER_AGENT = "wanderlens/0.1 (+https://github.com/Vengomatto/wanderlens)"

_SECTIONS = (("Regions", "region"), ("Cities", "city"), ("Other destinations", "other"))
_SKIP_PREFIXES = ("file:", "image:", "category:")
_TEMPLATE_RE = re.compile(
    r"\{\{\s*(?:marker|listing|see|do|go|sleep|eat|drink|buy|around)\b([^}]*)\}\}", re.I
)
_PARAM_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*((?:[^|{}\[\]]|\[\[[^\]]*\]\])*)")
_LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def _template_params(body: str) -> dict[str, str]:
    """Parse template params without splitting on '|' inside [[links]]."""
    params: dict[str, str] = {}
    for key, value in _PARAM_RE.findall(body):
        params.setdefault(key.strip().lower(), value.strip())
    return params


def _section_body(wikitext: str, section: str) -> str:
    match = re.search(
        rf"==+\s*{re.escape(section)}\s*==+(.*?)(?=\n==[^=]|\Z)", wikitext, re.S | re.I
    )
    return match.group(1) if match else ""


def _to_float(value: Optional[str]) -> Optional[float]:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _clean_title(value: str) -> str:
    """Strip wiki link markup and fragments from a marker's name value."""
    value = (value or "").strip().replace("[[", "").replace("]]", "")
    if "|" in value:
        value = value.split("|", 1)[1]
    return value.split("#", 1)[0].strip()


def _template_entry(template: str, granularity: str) -> Optional[dict]:
    body = template[2:-2] if template.endswith("}}") else template
    params = _template_params(body)
    title = _clean_title(params.get("name") or params.get("title"))
    if not title:
        return None
    return {
        "title": title,
        "granularity": granularity,
        "lat": _to_float(params.get("lat")),
        "lon": _to_float(params.get("long") or params.get("lon")),
        "qid": params.get("wikidata", "").strip(),
    }


def parse_section_entries(body: str, granularity: str) -> list[dict]:
    """List-item and marker/listing entries in a section body."""
    entries: list[dict] = []
    for line in body.splitlines():
        if not re.match(r"^\s*[*#]", line):
            continue
        template = _TEMPLATE_RE.search(line)
        if template:
            entry = _template_entry(template.group(0), granularity)
            if entry:
                entries.append(entry)
                continue
        link = _LINK_RE.search(line)
        if link:
            title = link.group(1).strip()
            if title and not title.lower().startswith(_SKIP_PREFIXES):
                entries.append(
                    {"title": title, "granularity": granularity, "lat": None, "lon": None, "qid": ""}
                )
    return entries


def country_destination_entries(
    wikitext: str, country: str = "", foreign: Optional[set[str]] = None
) -> list[dict]:
    """Deduplicated entries across sections, granularity from the section."""
    foreign = {name.lower() for name in (foreign or set())}
    if country:
        foreign.add(country.lower())
    entries: list[dict] = []
    seen: set[str] = set()
    for section, granularity in _SECTIONS:
        for entry in parse_section_entries(_section_body(wikitext, section), granularity):
            title = entry["title"]
            key = title.lower()
            if key in seen or key in foreign:
                continue
            seen.add(key)
            entries.append(entry)
    return entries


def country_destination_titles(wikitext: str) -> list[tuple[str, str]]:
    """(title, granularity) pairs from a country page's sections."""
    return [(e["title"], e["granularity"]) for e in country_destination_entries(wikitext)]


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
                "prop": "coordinates|extracts|pageprops",
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


def build_country_destinations(
    country: str,
    session=None,
    timeout: int = 30,
    min_extract_chars: int = 0,
    foreign: Optional[set[str]] = None,
    log=None,
) -> list[Destination]:
    wikitext = _fetch_wikitext(country, session=session, timeout=timeout)
    entries = country_destination_entries(wikitext, country=country, foreign=foreign)
    if not entries:
        return []
    by_title = {entry["title"]: entry for entry in entries}

    destinations: list[Destination] = []
    for page in _fetch_pages([entry["title"] for entry in entries], session=session, timeout=timeout):
        title = page.get("title", "")
        entry = by_title.get(title) or by_title.get(title.split(" (")[0], {})
        coordinates = page.get("coordinates") or []
        lat = float(coordinates[0]["lat"]) if coordinates else entry.get("lat")
        lon = float(coordinates[0]["lon"]) if coordinates else entry.get("lon")
        if lat is None or lon is None:
            if log is not None:
                log.append((title, "no coordinates"))
            continue
        extract = " ".join((page.get("extract") or "").split())[:300]
        if min_extract_chars and len(extract) < min_extract_chars:
            if log is not None:
                log.append((title, "short extract"))
            continue
        qid = (page.get("pageprops") or {}).get("wikibase_item") or entry.get("qid", "")
        destinations.append(
            Destination(
                id=f"wv:{title}",
                name=title,
                lat=lat,
                lon=lon,
                country=country,
                description=extract,
                granularity=entry.get("granularity", "other"),
                wikidata_id=qid,
            )
        )
    return destinations


def build_wikivoyage_catalog(
    countries: Iterable[str],
    session=None,
    timeout: int = 30,
    min_extract_chars: int = 0,
    log=None,
) -> JsonCatalog:
    countries = list(countries)
    foreign = set(countries)
    destinations: list[Destination] = []
    for country in countries:
        try:
            destinations.extend(
                build_country_destinations(
                    country,
                    session=session,
                    timeout=timeout,
                    min_extract_chars=min_extract_chars,
                    foreign=foreign,
                    log=log,
                )
            )
        except Exception:
            continue
    return JsonCatalog(destinations)
