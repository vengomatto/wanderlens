from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Photo:
    id: str
    source: str
    path: str
    sha256: str
    taken_at: Optional[datetime] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class Trip:
    id: int
    photos: list[Photo] = field(default_factory=list)
    country: Optional[str] = None
    city: Optional[str] = None


@dataclass
class Destination:
    id: str
    name: str
    lat: float
    lon: float
    country: str = ""
    attributes: list[str] = field(default_factory=list)
    description: str = ""
    granularity: str = ""


@dataclass
class Recommendation:
    destination: Destination
    score: float
    rank: int
    explanation: str = ""
    embedding_score: Optional[float] = None
    attribute_score: Optional[float] = None
    best_trip_id: Optional[int] = None
    best_trip_label: str = ""
    best_facet_similarity: Optional[float] = None
    matched_attributes: dict[str, float] = field(default_factory=dict)
    nearest_trip_km: Optional[float] = None
    popularity: Optional[float] = None
    popularity_label: str = ""


@dataclass
class Facet:
    """A taste facet: one visual centroid per Trip, with the Trip's identity."""

    trip_id: Optional[int]
    label: str
    vector: object
    weight: float = 1.0


@dataclass
class TasteProfile:
    user_id: int
    geography: dict[str, float] = field(default_factory=dict)
    tags: dict[str, float] = field(default_factory=dict)
    embedding: Optional[object] = None


@dataclass
class MediaImage:
    url: str
    source: str = ""
    license: str = ""
    attribution: str = ""


@dataclass
class DestinationMedia:
    destination_id: str
    title: str = ""
    page_url: str = ""
    extract: str = ""
    source: str = ""
    license: str = ""
    attribution: str = ""
    images: list[MediaImage] = field(default_factory=list)
    region_geojson: str = ""
    region_kind: str = ""
    region_radius_km: Optional[float] = None
