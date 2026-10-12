from __future__ import annotations

from typing import Callable, Iterable, Optional

import numpy as np

from wanderlens.core.models import Destination, Facet, Recommendation, TasteProfile
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


def matched_attributes(
    taste_weights: dict[str, float], destination: Destination
) -> dict[str, float]:
    """Canonical attributes the destination shares with the profile, by weight."""
    attributes = destination_attribute_set(destination)
    return {
        attribute: taste_weights[attribute]
        for attribute in attributes
        if taste_weights.get(attribute)
    }


def nearest_visited_km(
    destination: Destination, centers: Iterable[tuple[float, float]]
) -> Optional[float]:
    centers = list(centers)
    if not centers or destination.lat is None or destination.lon is None:
        return None
    return min(
        haversine_km(destination.lat, destination.lon, clat, clon)
        for clat, clon in centers
    )


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


def _as_facets(taste_facets) -> list[Facet]:
    facets: list[Facet] = []
    for item in taste_facets or []:
        if isinstance(item, Facet):
            facets.append(item)
        else:
            facets.append(Facet(trip_id=None, label="", vector=item))
    return facets


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
    visited_centers: Iterable[tuple[float, float]] = (),
) -> list[Recommendation]:
    """Deterministic ranking, excluding visited countries.

    ``vectors`` (destination id -> embedding) lets callers supply cached
    embeddings; missing entries fall back to ``embed_text(destination_text(...))``.
    When ``taste_tags`` is given, the score blends embedding similarity
    (``alpha``) with a canonical-attribute match (``1 - alpha``). When
    ``taste_facets`` is given, the embedding score is the best match over the
    per-trip facets (max), so distinct tastes are not averaged away; each facet
    may be a :class:`Facet` (carrying its Trip) or a bare vector.
    """
    excluded = {c.lower() for c in exclude_countries}
    facets = _as_facets(taste_facets)
    centers = list(visited_centers)
    scored: list[tuple] = []
    for destination in destinations:
        if destination.country.lower() in excluded:
            continue
        if vectors is not None and destination.id in vectors:
            vector = vectors[destination.id]
        else:
            if embed_text is None:
                raise ValueError("embed_text is required when embeddings are not cached")
            vector = embed_text(destination_text(destination))

        best_trip_id: Optional[int] = None
        best_trip_label = ""
        best_facet_similarity: Optional[float] = None
        if facets:
            similarities = [(float(np.dot(facet.vector, vector)), facet) for facet in facets]
            embedding_score, best = max(similarities, key=lambda item: item[0])
            best_trip_id = best.trip_id
            best_trip_label = best.label
            best_facet_similarity = embedding_score
        elif taste is not None:
            embedding_score = float(np.dot(taste, vector))
        else:
            embedding_score = 0.0

        if taste_tags:
            attributes = matched_attributes(taste_tags, destination)
            attribute_score = sum(attributes.values())
            score = alpha * embedding_score + (1.0 - alpha) * attribute_score
        else:
            attributes = {}
            attribute_score = None
            score = embedding_score

        scored.append(
            (
                score,
                embedding_score,
                attribute_score,
                destination,
                best_trip_id,
                best_trip_label,
                best_facet_similarity,
                attributes,
                nearest_visited_km(destination, centers),
            )
        )
    scored.sort(key=lambda row: (-row[0], row[3].name))

    ranked = scored[:top_k] if top_k is not None else scored
    return [
        Recommendation(
            destination=destination,
            score=score,
            rank=index,
            embedding_score=embedding_score,
            attribute_score=attribute_score,
            best_trip_id=best_trip_id,
            best_trip_label=best_trip_label,
            best_facet_similarity=best_facet_similarity,
            matched_attributes=attributes,
            nearest_trip_km=nearest,
        )
        for index, (
            score,
            embedding_score,
            attribute_score,
            destination,
            best_trip_id,
            best_trip_label,
            best_facet_similarity,
            attributes,
            nearest,
        ) in enumerate(ranked, start=1)
    ]


def explain(
    rec: Recommendation,
    profile: TasteProfile,
    visited_country: Optional[str] = None,
) -> str:
    parts: list[str] = []
    if rec.best_trip_label:
        if rec.best_facet_similarity is not None:
            parts.append(
                f"closest to your {rec.best_trip_label} trip "
                f"(similarity {rec.best_facet_similarity:.2f})"
            )
        else:
            parts.append(f"closest to your {rec.best_trip_label} trip")
    top_attributes = sorted(rec.matched_attributes.items(), key=lambda item: -item[1])[:3]
    if top_attributes:
        names = ", ".join(name for name, _ in top_attributes)
        parts.append(f"shares {names} with your taste")
    if rec.nearest_trip_km is not None:
        parts.append(f"new for you — no visit within {int(rec.nearest_trip_km)} km")
    if parts:
        return f"{rec.destination.name} fits: " + "; ".join(parts) + "."

    labels = [t[0] for t in sorted(profile.tags.items(), key=lambda item: -item[1])[:3]]
    if labels:
        return f"{rec.destination.name} matches your taste for " + ", ".join(labels) + "."
    if visited_country:
        return f"{rec.destination.name} fits the character of your {visited_country} trips."
    return f"{rec.destination.name} matches your overall photo profile."
