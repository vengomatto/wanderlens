from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from wanderlens.core.models import Destination

_QUALIFIER_RE = re.compile(r"\s*\([^)]*\)\s*$")
GRANULARITIES = ("city", "region", "area")
_GRANULARITY_MAP = {"other": "area", "town": "city", "municipality": "city"}


def clean_name(name: str) -> str:
    """Strip a trailing parenthetical qualifier and normalize uniform casing.

    Names that already mix case (e.g. "Costa del Sol") are left untouched, so
    proper nouns and connectors survive.
    """
    cleaned = _QUALIFIER_RE.sub("", name or "").strip()
    if not cleaned:
        return (name or "").strip()
    if cleaned == cleaned.upper() or cleaned == cleaned.lower():
        cleaned = " ".join(
            word[0].upper() + word[1:] if word else word for word in cleaned.split()
        )
    return cleaned


def bound_granularity(value: str) -> str:
    value = (value or "").strip().lower()
    if value in GRANULARITIES:
        return value
    if not value:
        return ""
    return _GRANULARITY_MAP.get(value, "area")


def clean_destination(destination: Destination) -> Destination:
    destination.name = clean_name(destination.name)
    destination.granularity = bound_granularity(destination.granularity)
    return destination


def dedupe(destinations: Iterable[Destination]) -> list[Destination]:
    """Drop duplicate (normalized name, country), keeping the first."""
    seen: set[tuple[str, str]] = set()
    kept: list[Destination] = []
    for destination in destinations:
        key = (destination.name.lower(), destination.country.lower())
        if key in seen:
            continue
        seen.add(key)
        kept.append(destination)
    return kept


def destination_to_dict(destination: Destination) -> dict:
    return {
        "id": destination.id,
        "name": destination.name,
        "lat": destination.lat,
        "lon": destination.lon,
        "country": destination.country,
        "attributes": list(destination.attributes),
        "description": destination.description,
        "granularity": destination.granularity,
    }


def destination_from_dict(data: dict) -> Destination:
    return clean_destination(
        Destination(
            id=str(data["id"]),
            name=data["name"],
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            country=data.get("country", ""),
            attributes=list(data.get("attributes", [])),
            description=data.get("description", ""),
            granularity=data.get("granularity", ""),
        )
    )


def normalize_record(source: str, raw: dict) -> Destination:
    """Normalize a Wikidata or GeoNames record into a Destination."""
    if source == "wikidata":
        return clean_destination(
            Destination(
                id=f"wd:{raw['id']}",
                name=raw["label"],
                lat=float(raw["lat"]),
                lon=float(raw["lon"]),
                country=raw.get("country", ""),
                attributes=list(raw.get("tags", [])),
                description=raw.get("description", ""),
            )
        )
    if source == "geonames":
        return clean_destination(
            Destination(
                id=f"gn:{raw['geonameId']}",
                name=raw["name"],
                lat=float(raw["latitude"]),
                lon=float(raw["longitude"]),
                country=raw.get("countryName", ""),
                attributes=list(raw.get("tags", [])),
                description=raw.get("description", ""),
            )
        )
    raise ValueError(f"unknown source: {source}")


def catalog_from_records(records: dict[str, Iterable[dict]]) -> "JsonCatalog":
    destinations: list[Destination] = []
    for source, items in records.items():
        for raw in items:
            destinations.append(normalize_record(source, raw))
    return JsonCatalog(destinations)


class JsonCatalog:
    """A local, bulk-cached pool of candidate Destinations."""

    def __init__(self, destinations: Iterable[Destination] = ()):
        self._destinations = dedupe(clean_destination(d) for d in destinations)

    @classmethod
    def load(cls, path: str | Path) -> "JsonCatalog":
        data = json.loads(Path(path).read_text())
        return cls(destination_from_dict(item) for item in data)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([destination_to_dict(d) for d in self._destinations], indent=2))

    def candidates(self, area: str | None = None) -> list[Destination]:
        if area is None:
            return list(self._destinations)
        return [d for d in self._destinations if d.country.lower() == area.lower()]

    def add(self, destination: Destination) -> None:
        self._destinations.append(destination)

    def __len__(self) -> int:
        return len(self._destinations)
