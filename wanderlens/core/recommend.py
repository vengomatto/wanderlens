from __future__ import annotations

import math
from typing import Callable, Iterable, Optional

import numpy as np

from wanderlens.core.models import Destination, Facet, Recommendation, TasteProfile
from wanderlens.core.climate import season_overlap
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


def attribute_idf(destinations: Iterable[Destination]) -> dict[str, float]:
    """Specificity of each canonical attribute across the candidate catalog.

    A smoothed inverse-document-frequency term, normalized to mean 1, so a rare,
    descriptive attribute counts for more than one that appears everywhere.
    Deterministic for a given catalog.
    """
    attribute_sets = [destination_attribute_set(destination) for destination in destinations]
    count = len(attribute_sets)
    if not count:
        return {}
    document_frequency: dict[str, int] = {}
    for attributes in attribute_sets:
        for attribute in attributes:
            document_frequency[attribute] = document_frequency.get(attribute, 0) + 1
    raw = {
        attribute: math.log((count + 1) / (frequency + 1)) + 1.0
        for attribute, frequency in document_frequency.items()
    }
    if not raw:
        return {}
    mean = sum(raw.values()) / len(raw)
    if not mean:
        return raw
    return {attribute: value / mean for attribute, value in raw.items()}


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


def _cosine(a, b) -> float:
    if a is None or b is None:
        return 0.0
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if not na or not nb:
        return 0.0
    return float(np.dot(a, b)) / (na * nb)


def normalize_popularity(total: Optional[float]) -> Optional[float]:
    if total is None:
        return None
    return min(1.0, max(0.0, math.log10(total + 1) / 6.0))


def popularity_label(score: Optional[float]) -> str:
    if score is None:
        return ""
    if score >= 0.66:
        return "famous"
    if score <= 0.33:
        return "uncommon"
    return "balanced"


def percentile_labels(scores: dict[str, float]) -> dict[str, str]:
    """Label a pool by percentile: top third famous, bottom third uncommon."""
    values = sorted(scores.values())
    count = len(values)
    if count < 3:
        return {key: popularity_label(value) for key, value in scores.items()}
    lower = values[count // 3]
    upper = values[(2 * count) // 3]
    labels: dict[str, str] = {}
    for key, value in scores.items():
        if value >= upper:
            labels[key] = "famous"
        elif value <= lower:
            labels[key] = "uncommon"
        else:
            labels[key] = "balanced"
    return labels


def _minmax(values: list[float]) -> list[float]:
    low, high = min(values), max(values)
    if high <= low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def _calibrate(scored: list[tuple], alpha: float) -> None:
    """Rescale embedding/attribute per pool so the blend is not scale-dominated."""
    embedding_norm = _minmax([row[1] for row in scored])
    has_attribute = any(row[2] is not None for row in scored)
    attribute_norm = (
        _minmax([row[2] if row[2] is not None else 0.0 for row in scored])
        if has_attribute
        else None
    )
    for index, row in enumerate(scored):
        if row[2] is None or attribute_norm is None:
            base = embedding_norm[index]
        else:
            base = alpha * embedding_norm[index] + (1.0 - alpha) * attribute_norm[index]
        scored[index] = (base + row[10],) + row[1:]


def _select(rows: list[tuple], top_k: Optional[int], diversity: float) -> list[tuple]:
    if not rows:
        return []
    ordered = sorted(rows, key=lambda row: (-row[0], row[3].name))
    if not diversity or top_k is None:
        return ordered[:top_k] if top_k is not None else ordered

    remaining = list(ordered)
    selected = [remaining.pop(0)]
    while remaining and len(selected) < top_k:
        best_index = 0
        best_value = None
        for index, row in enumerate(remaining):
            similarity = max(
                (_cosine(row[-1], chosen[-1]) for chosen in selected), default=0.0
            )
            value = row[0] - diversity * similarity
            if (
                best_value is None
                or value > best_value
                or (value == best_value and row[3].name < remaining[best_index][3].name)
            ):
                best_value = value
                best_index = index
        selected.append(remaining.pop(best_index))
    return selected


def rank_destinations(
    taste: Optional[np.ndarray],
    destinations: Iterable[Destination],
    embed_text: Optional[Callable[[str], np.ndarray]] = None,
    exclude_countries: Iterable[str] = (),
    top_k: Optional[int] = None,
    vectors: Optional[dict] = None,
    taste_tags: Optional[dict[str, float]] = None,
    alpha: float = 0.25,
    taste_facets: Optional[list] = None,
    visited_centers: Iterable[tuple[float, float]] = (),
    diversity: float = 0.0,
    novelty: str = "balanced",
    popularity: Optional[dict[str, float]] = None,
    novelty_weight: float = 0.15,
    feedback: Optional[dict[str, str]] = None,
    feedback_weight: float = 0.15,
    climate: Optional[dict[str, float]] = None,
    climate_weight: float = 0.0,
    season: Optional[str] = None,
    best_months: Optional[dict[str, list]] = None,
    image_vectors: Optional[dict] = None,
    calibrate: bool = False,
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
    destinations = list(destinations)
    idf = attribute_idf(destinations) if taste_tags else {}
    pool_labels = percentile_labels(popularity) if popularity else {}
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
            score_vector = (
                image_vectors.get(destination.id)
                if image_vectors and destination.id in image_vectors
                else vector
            )
            similarities = [
                (float(np.dot(facet.vector, score_vector)) * getattr(facet, "weight", 1.0), facet)
                for facet in facets
            ]
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
            attribute_score = sum(
                weight * idf.get(attribute, 1.0)
                for attribute, weight in attributes.items()
            )
        else:
            attributes = {}
            attribute_score = None

        delta = 0.0
        pop = popularity.get(destination.id) if popularity else None
        if pop is not None and novelty in {"familiar", "uncommon"}:
            delta += novelty_weight * (pop - 0.5) * (1 if novelty == "familiar" else -1)

        action = feedback.get(destination.id) if feedback else None
        if action in {"like", "save"}:
            delta += feedback_weight
        elif action in {"dislike", "skip"}:
            delta -= feedback_weight

        if climate is not None and climate_weight:
            delta += climate_weight * climate.get(destination.id, 0.0)
        if season and best_months:
            if season_overlap(best_months.get(destination.id, []), season):
                delta += max(climate_weight, 0.05)

        if taste_tags:
            base = alpha * embedding_score + (1.0 - alpha) * attribute_score
        else:
            base = embedding_score

        scored.append(
            (
                base + delta,
                embedding_score,
                attribute_score,
                destination,
                best_trip_id,
                best_trip_label,
                best_facet_similarity,
                attributes,
                nearest_visited_km(destination, centers),
                pop,
                delta,
                vector,
            )
        )

    if calibrate and scored:
        _calibrate(scored, alpha)

    ranked = _select(scored, top_k, diversity)
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
            popularity=pop,
            popularity_label=pool_labels.get(destination.id) or popularity_label(pop),
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
            pop,
            _delta,
            vector,
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
