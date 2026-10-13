from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from wanderlens.core.models import Destination, DestinationMedia, Photo


class PhotoSource(Protocol):
    """A source of a Photo Archive. Implementations must not leak their
    backing technology into callers; only ``iter_photos`` is observed."""

    name: str

    def iter_photos(self) -> Iterable[Photo]:
        ...


class EmbeddingModel(Protocol):
    dim: int

    def embed_image(self, path: str) -> "object":
        ...

    def embed_text(self, text: str) -> "object":
        ...


class VisionModel(Protocol):
    def describe(self, paths: Sequence[str]) -> list[str]:
        ...


class PlaceCatalog(Protocol):
    def candidates(self, area: str | None = None) -> Iterable[Destination]:
        ...


class DescriptionProvider(Protocol):
    """Supplies a short description for a place. Must return ``None`` on a miss
    (never raise) so a provider chain can continue."""

    name: str

    def describe(self, name: str, country: str) -> "str | None":
        ...


class DestinationMediaProvider(Protocol):
    """Supplies images and an expanded description for a Destination. Must return
    ``None`` on a miss (never raise) so a provider chain can continue."""

    name: str

    def fetch(self, destination: Destination) -> "DestinationMedia | None":
        ...


class TasteEnricher(Protocol):
    """Derives structured trip attributes and a richer destination description.
    Injectable and pinned; a failure must fall back to the deterministic text."""

    name: str
    prompt_version: str

    def attribute_trip(self, tags, context: str = "") -> list[str]:
        ...

    def description(self, destination: Destination) -> str:
        ...


class ExplanationSynthesizer(Protocol):
    """Turns a Recommendation's evidence into a short explanation. Injectable and
    pinned; a failure must fall back to the deterministic explanation."""

    name: str
    prompt_version: str

    def synthesize(self, evidence: dict) -> str:
        ...


class ItinerarySynthesizer(Protocol):
    """Synthesises a day-by-day itinerary from gathered points of interest.
    Injectable and pinned; a failure must leave the run without an itinerary."""

    name: str
    prompt_version: str

    def synthesize(self, destination: Destination, pois: list, days: int) -> list:
        ...
