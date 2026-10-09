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
