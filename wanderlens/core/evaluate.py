from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

import numpy as np


@dataclass
class HoldoutResult:
    holdout: str
    rank: int | None
    within_top: int

    @property
    def passed(self) -> bool:
        return self.rank is not None and self.rank <= self.within_top

    def describe(self) -> str:
        if self.rank is None:
            return f"Held-out place '{self.holdout}' did not resurface in the catalog."
        verdict = "PASS" if self.passed else "FAIL"
        return (
            f"Held-out place '{self.holdout}' resurfaced at rank {self.rank} "
            f"(top {self.within_top}) — {verdict}"
        )


def evaluate_holdout(ranked, holdout: str, within_top: int) -> HoldoutResult:
    for recommendation in ranked:
        if recommendation.destination.country.lower() == holdout.lower():
            return HoldoutResult(holdout=holdout, rank=recommendation.rank, within_top=within_top)
    return HoldoutResult(holdout=holdout, rank=None, within_top=within_top)


def evaluate_resurfacing(ranked, center, radius_km: float, within_top: int, label: str) -> HoldoutResult:
    """First ranked Destination within ``radius_km`` of ``center`` (lat, lon)."""
    from wanderlens.core.taste import haversine_km

    for recommendation in ranked:
        destination = recommendation.destination
        if haversine_km(destination.lat, destination.lon, center[0], center[1]) <= radius_km:
            return HoldoutResult(holdout=label, rank=recommendation.rank, within_top=within_top)
    return HoldoutResult(holdout=label, rank=None, within_top=within_top)


def precision_at_k(ranked_ids, relevant, k: int) -> float:
    """Fraction of the top-``k`` ranked ids that are relevant."""
    ids = list(ranked_ids)
    top = ids[:k]
    if not top or not relevant:
        return 0.0
    hits = sum(1 for item in top if item in relevant)
    return hits / len(top)


def mrr(ranked_ids, relevant) -> float:
    """Mean reciprocal rank of the first relevant item (0.0 when none appear)."""
    if not relevant:
        return 0.0
    for position, item in enumerate(ranked_ids, start=1):
        if item in relevant:
            return 1.0 / position
    return 0.0


def recall_at_k(rank: int | None, k: int) -> float:
    """1.0 when the relevant item appears within the top ``k``, else 0.0."""
    return 1.0 if rank is not None and rank <= k else 0.0


def mean_reciprocal_rank(ranks) -> float:
    """Average reciprocal rank over a list of ranks (``None`` = not found)."""
    ranks = list(ranks)
    if not ranks:
        return 0.0
    return sum(1.0 / rank for rank in ranks if rank) / len(ranks)


def check_regression(
    mrr_value: float,
    baseline_mrr: float,
    margin: float = 0.1,
    relative: bool = True,
    floor: float = 0.05,
) -> bool:
    """True when ``mrr_value`` is within ``margin`` of the baseline.

    The effective baseline is at least ``floor`` so a near-zero recorded baseline
    cannot make the gate impossible to fail. With ``relative`` the margin is a
    fraction of the baseline.
    """
    effective = max(baseline_mrr, floor)
    if relative:
        return mrr_value >= effective * (1.0 - margin)
    return mrr_value >= effective - margin


def collapsed_share(vectors) -> float:
    """Share of vectors that are near-identical (cosine > 0.99) to another."""
    array = [np.asarray(vector, dtype=np.float32) for vector in vectors if vector is not None]
    if len(array) < 2:
        return 0.0
    matrix = np.stack(
        [v / np.linalg.norm(v) if np.linalg.norm(v) else v for v in array]
    )
    similarities = matrix @ matrix.T
    np.fill_diagonal(similarities, -1.0)
    collapsed = int((similarities.max(axis=1) > 0.99).sum())
    return round(collapsed / len(array), 4)


def diagnostics(vectors, recommendations) -> dict:
    """Component spread, collapsed-vector share, and top-result mix."""

    def spread(values) -> float:
        vals = [v for v in values if v is not None]
        return round(float(np.std(vals)), 4) if vals else 0.0

    attributes = Counter(
        attribute for rec in recommendations for attribute in rec.matched_attributes
    )
    countries = Counter(rec.destination.country for rec in recommendations)
    return {
        "n": len(recommendations),
        "score_std": spread([rec.score for rec in recommendations]),
        "embedding_std": spread([rec.embedding_score for rec in recommendations]),
        "attribute_std": spread([rec.attribute_score for rec in recommendations]),
        "collapsed_share": collapsed_share(vectors),
        "top_attributes": attributes.most_common(5),
        "top_countries": countries.most_common(5),
    }
