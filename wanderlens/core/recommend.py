from __future__ import annotations

from typing import Callable, Iterable, Optional

import numpy as np

from wanderlens.core.models import Destination, Recommendation, TasteProfile


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
    taste: np.ndarray,
    destinations: Iterable[Destination],
    embed_text: Optional[Callable[[str], np.ndarray]] = None,
    exclude_countries: Iterable[str] = (),
    top_k: Optional[int] = None,
    vectors: Optional[dict] = None,
) -> list[Recommendation]:
    """Deterministic ranking by cosine similarity, excluding visited countries.

    ``vectors`` (destination id -> embedding) lets callers supply cached
    embeddings; missing entries fall back to ``embed_text(destination_text(...))``.
    """
    excluded = {c.lower() for c in exclude_countries}
    scored: list[tuple[float, Destination]] = []
    for destination in destinations:
        if destination.country.lower() in excluded:
            continue
        if vectors is not None and destination.id in vectors:
            vector = vectors[destination.id]
        else:
            if embed_text is None:
                raise ValueError("embed_text is required when embeddings are not cached")
            vector = embed_text(destination_text(destination))
        score = float(np.dot(taste, vector))
        scored.append((score, destination))
    scored.sort(key=lambda pair: (-pair[0], pair[1].name))

    ranked = scored[:top_k] if top_k is not None else scored
    return [
        Recommendation(destination=destination, score=score, rank=i)
        for i, (score, destination) in enumerate(ranked, start=1)
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
