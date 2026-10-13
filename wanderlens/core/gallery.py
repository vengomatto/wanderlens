from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from wanderlens.core.models import Destination, Facet

COASTAL = np.array([1.0, 0.0, 0.0], dtype=np.float32)
MOUNTAIN = np.array([0.0, 1.0, 0.0], dtype=np.float32)
CITY = np.array([0.0, 0.0, 1.0], dtype=np.float32)


@dataclass
class Gallery:
    """A reproducible synthetic photo archive and candidate catalog."""

    facets: list[Facet]
    taste_tags: dict[str, float]
    destinations: list[Destination]
    vectors: dict[str, np.ndarray]
    relevant: set[str]

    def to_json(self) -> str:
        """A stable, order-independent fingerprint of the fixture."""
        payload = {
            "facets": [
                {
                    "trip_id": facet.trip_id,
                    "label": facet.label,
                    "vector": [round(float(x), 6) for x in facet.vector],
                    "weight": round(float(facet.weight), 6),
                }
                for facet in self.facets
            ],
            "taste_tags": self.taste_tags,
            "destinations": [
                {
                    "id": d.id,
                    "name": d.name,
                    "country": d.country,
                    "attributes": list(d.attributes),
                    "description": d.description,
                }
                for d in self.destinations
            ],
            "vectors": {k: [round(float(x), 6) for x in v] for k, v in self.vectors.items()},
            "relevant": sorted(self.relevant),
        }
        return json.dumps(payload, sort_keys=True, ensure_ascii=False)


def _trip(trip_id: int, label: str, vector, weight: float = 1.0) -> Facet:
    return Facet(trip_id=trip_id, label=label, vector=vector.copy(), weight=weight)


def build_gallery() -> Gallery:
    """Build a deterministic coastal-vs-mountain fixture.

    The taste is coastal (three well-supported coastal trips plus one mountain
    trip), and the catalog mixes three coastal destinations that should surface
    with several distractors.
    """
    facets = [
        _trip(0, "Algarve, Portugal", COASTAL),
        _trip(1, "Puglia, Italy", COASTAL),
        _trip(2, "Dalmatia, Croatia", COASTAL),
        _trip(3, "Dolomites, Italy", MOUNTAIN),
    ]
    taste_tags = {"coastal": 0.6, "water": 0.4}

    coastal = [
        Destination(id="rel-1", name="Lagos", lat=37.1, lon=-8.67, country="Portugal", attributes=["coastal"], description="a coastal town with beaches"),
        Destination(id="rel-2", name="Lecce", lat=40.35, lon=18.17, country="Italy", attributes=["coastal"], description="a coastal town in the south"),
        Destination(id="rel-3", name="Hvar", lat=43.17, lon=16.44, country="Croatia", attributes=["coastal"], description="a coastal island town"),
    ]
    distractors = [
        Destination(id="dis-1", name="Zermatt", lat=46.02, lon=7.75, country="Switzerland", attributes=["mountains"], description="an alpine mountain village"),
        Destination(id="dis-2", name="Innsbruck", lat=47.27, lon=11.39, country="Austria", attributes=["mountains"], description="an alpine city surrounded by peaks"),
        Destination(id="dis-3", name="Milan", lat=45.46, lon=9.19, country="Italy", attributes=["city"], description="a busy urban metropolis"),
        Destination(id="dis-4", name="Munich", lat=48.14, lon=11.58, country="Germany", attributes=["city"], description="a large city of museums"),
        Destination(id="dis-5", name="Vienna", lat=48.21, lon=16.37, country="Austria", attributes=["city"], description="a historic city of palaces"),
    ]
    destinations = coastal + distractors

    vectors = {d.id: (COASTAL if d in coastal else MOUNTAIN if d.attributes == ["mountains"] else CITY).copy() for d in destinations}

    return Gallery(
        facets=facets,
        taste_tags=taste_tags,
        destinations=destinations,
        vectors=vectors,
        relevant={d.id for d in coastal},
    )
