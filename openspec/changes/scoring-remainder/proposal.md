# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A3 remainder, L8/L9/L5): every trip is weighted
equally regardless of when it happened (recency) or how much it was engaged with,
nothing penalises a destination that matches only attributes the user has never
shown interest in, and the first ranking pass only considers ~20 candidates so a
season/novelty preference cannot promote a place outside that bubble.

## What Changes

- **Recency-weighted facets.** A trip's facet can decay by age (a configurable
  half-life), so recent trips count more; off by default.
- **Optional anti-match penalty.** A small, capped penalty for a destination that
  matches only catalog-common attributes absent from the profile; off by default.
- **Configurable candidate pre-filter.** The pre-ranking pool floor becomes a
  setting (default unchanged) so all terms can act over a larger pool.
- No **BREAKING** changes; all new terms are off by default.

## Capabilities

### Modified Capabilities
- `recommendation`: accumulates recency weighting, an optional anti-match penalty,
  and a configurable pre-filter.

## Impact

- `wanderlens/core/recommend.py`: an `anti_match` term.
- `wanderlens/pipeline/recommend.py`: recency in facets, pre-filter size, wiring.
- `wanderlens/config.py`, `cli/main.py`.
- Tests for each.
