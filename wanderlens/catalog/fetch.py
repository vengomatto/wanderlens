from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from wanderlens.catalog.destinations import JsonCatalog, normalize_record

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


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
