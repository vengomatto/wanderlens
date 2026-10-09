from __future__ import annotations

from typing import Callable, Iterable, Optional

import numpy as np

from wanderlens.core.models import Destination, Recommendation, TasteProfile
from wanderlens.core.taste import haversine_km
from wanderlens.core.vocabulary import canonicalize


def filter_unvisited_proximity(
    destinations: Iterable[Destination],
    centers: Iterable[tuple[float, float]],
    radius_km: float,
) -> list[Destination]:
    """Keep Destinations farther than ``radius_km`` from every visited center."""
    centers = list(centers)
    if not centers:
        return list(destinations)
    kept: list[Destination] = []
    for destination in destinations:
        if all(
            haversine_km(destination.lat, destination.lon, clat, clon) > radius_km
            for clat, clon in centers
        ):
            kept.append(destination)
    return kept


def taste_attribute_weights(tags: dict[str, float]) -> dict[str, float]:
    """Aggregate free-text subject tags into normalized canonical attributes."""
    accumulated: dict[str, float] = {}
    for tag, weight in tags.items():
        for attribute in canonicalize(tag):
            accumulated[attribute] = accumulated.get(attribute, 0.0) + weight
    total = sum(accumulated.values())
    if not total:
        return {}
    return {attribute: weight / total for attribute, weight in accumulated.items()}


def destination_attribute_set(destination: Destination) -> set[str]:
    text = f"{destination.name} {destination.description} " + " ".join(destination.attributes)
    return set(canonicalize(text))


def _attribute_match(taste_weights: dict[str, float], destination: Destination) -> float:
    attributes = destination_attribute_set(destination)
    return sum(taste_weights.get(attribute, 0.0) for attribute in attributes)


def taste_embedding(vectors: Iterable[np.ndarray]) -> Optional[np.ndarray]:
    stack = [v for v in vectors if v is not None]
    if not stack:
        return None
    mean = np.mean(np.stack(stack), axis=0).astype(np.float32)
    norm = np.linalg.norm(mean)
    return mean / norm if norm else mean


def destination_text(destination: Destination) -> str:
    text = destination.description or f"{destination.name}, {destination.country}"
    if destination.attributes:
        text = f"{text}, " + ", ".join(destination.attributes)
    return text


def rank_destinations(
    taste: Optional[np.ndarray],
    destinations: Iterable[Destination],
    embed_text: Optional[Callable[[str], np.ndarray]] = None,
    exclude_countries: Iterable[str] = (),
    top_k: Optional[int] = None,
    vectors: Optional[dict] = None,
    taste_tags: Optional[dict[str, float]] = None,
    alpha: float = 0.5,
    taste_facets: Optional[list] = None,
) -> list[Recommendation]:
    """Deterministic ranking, excluding visited countries.

    ``vectors`` (destination id -> embedding) lets callers supply cached
    embeddings; missing entries fall back to ``embed_text(destination_text(...))``.
    When ``taste_tags`` is given, the score blends embedding similarity
    (``alpha``) with a canonical-attribute match (``1 - alpha``). When
    ``taste_facets`` is given, the embedding score is the best match over the
    per-trip facets (max), so distinct tastes are not averaged away.
    """
    excluded = {c.lower() for c in exclude_countries}
    scored: list[tuple[float, float, float, Destination]] = []
    for destination in destinations:
        if destination.country.lower() in excluded:
            continue
        if vectors is not None and destination.id in vectors:
            vector = vectors[destination.id]
        else:
            if embed_text is None:
                raise ValueError("embed_text is required when embeddings are not cached")
            vector = embed_text(destination_text(destination))
        if taste_facets:
            embedding_score = max(float(np.dot(facet, vector)) for facet in taste_facets)
        elif taste is not None:
            embedding_score = float(np.dot(taste, vector))
        else:
            embedding_score = 0.0
        if taste_tags:
            attribute_score = _attribute_match(taste_tags, destination)
            score = alpha * embedding_score + (1.0 - alpha) * attribute_score
        else:
            attribute_score = None
            score = embedding_score
        scored.append((score, embedding_score, attribute_score, destination))
    scored.sort(key=lambda row: (-row[0], row[3].name))

    ranked = scored[:top_k] if top_k is not None else scored
    return [
        Recommendation(
            destination=destination,
            score=score,
            rank=index,
            embedding_score=embedding_score,
            attribute_score=attribute_score,
        )
        for index, (score, embedding_score, attribute_score, destination) in enumerate(ranked, start=1)
    ]


def explain(destination: Destination, profile: TasteProfile, visited_country: Optional[str] = None) -> str:
    labels = [t[0] for t in sorted(profile.tags.items(), key=lambda item: -item[1])[:3]]
    reasons = []
    if labels:
        reasons.append("your taste for " + ", ".join(labels))
    if visited_country:
        reasons.append(f"the character of your {visited_country} trips")
    if not reasons:
        return f"{destination.name} matches your overall photo profile."
    return f"{destination.name} fits " + " and ".join(reasons) + "."
