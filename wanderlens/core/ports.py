from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from wanderlens.core.models import Destination, Photo


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
