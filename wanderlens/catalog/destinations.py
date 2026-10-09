from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from wanderlens.core.models import Destination


def destination_to_dict(destination: Destination) -> dict:
    return {
        "id": destination.id,
        "name": destination.name,
        "lat": destination.lat,
        "lon": destination.lon,
        "country": destination.country,
        "attributes": list(destination.attributes),
        "description": destination.description,
    }


def destination_from_dict(data: dict) -> Destination:
    return Destination(
        id=str(data["id"]),
        name=data["name"],
        lat=float(data["lat"]),
        lon=float(data["lon"]),
        country=data.get("country", ""),
        attributes=list(data.get("attributes", [])),
        description=data.get("description", ""),
    )


def normalize_record(source: str, raw: dict) -> Destination:
    """Normalize a Wikidata or GeoNames record into a Destination."""
    if source == "wikidata":
        return Destination(
            id=f"wd:{raw['id']}",
            name=raw["label"],
            lat=float(raw["lat"]),
            lon=float(raw["lon"]),
            country=raw.get("country", ""),
            attributes=list(raw.get("tags", [])),
            description=raw.get("description", ""),
        )
    if source == "geonames":
        return Destination(
            id=f"gn:{raw['geonameId']}",
            name=raw["name"],
            lat=float(raw["latitude"]),
            lon=float(raw["longitude"]),
            country=raw.get("countryName", ""),
            attributes=list(raw.get("tags", [])),
            description=raw.get("description", ""),
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
        self._destinations = list(destinations)

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
