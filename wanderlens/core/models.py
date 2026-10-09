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


@dataclass
class TasteProfile:
    user_id: int
    geography: dict[str, float] = field(default_factory=dict)
    tags: dict[str, float] = field(default_factory=dict)
    embedding: Optional[object] = None
