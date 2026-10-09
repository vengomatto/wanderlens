from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog, normalize_record

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
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


def default_description(record: dict) -> str:
    name = record.get("name", "")
    country = record.get("countryName", "")
    try:
        summary = fetch_wikipedia_summary(name, country)
        if summary:
            return summary
    except Exception:
        pass
    try:
        return fetch_wikidata_description(name)
    except Exception:
        return ""


def enrich_records(records: list[dict], fetch=None, delay: float = 0.0) -> list[dict]:
    """Attach a description to each record that lacks one; never fail the batch."""
    import time

    fetch = fetch or default_description
    for record in records:
        if record.get("description"):
            continue
        try:
            record["description"] = fetch(record) or ""
        except Exception:
            record["description"] = ""
        if delay:
            time.sleep(delay)
    return records


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
