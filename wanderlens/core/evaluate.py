from __future__ import annotations

from dataclasses import dataclass


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
