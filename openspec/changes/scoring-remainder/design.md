# Design

## Context

See `proposal.md`. Facets carry a `weight` (photo-count based). `attribute_idf`
gives per-catalog specificity. `run_recommend` computes a shortlist with
`min(len(candidates), max(count*4, 20))`.

## Decisions

### Recency on the facet weight
`load_taste_facets` reads the trip's `start_at`; when `recency_half_life_days > 0`
it multiplies the facet weight by `0.5 ** (age_days / half_life)` (age from now,
clamped at 1.0). Off by default, so existing behaviour is unchanged.

### Anti-match penalty
`rank_destinations(..., anti_match_weight=0.0)`: for a destination, sum the IDF
weight of its canonical attributes that are *not* in the profile and are catalog-
common (df over half the pool), and subtract `anti_match_weight * min(1,
share_of_common_unmatched)` capped at the weight. Off by default; deterministic.

### Configurable pre-filter
`candidate_prefilter` (config/CLI) sets the floor: `shortlist_size =
max(count*4, candidate_prefilter)`, still bounded by the candidate count. Default
stays 20 so nothing changes unless raised.

## Risks / Trade-offs

- **Recency can over-weight a single recent trip** → off by default, half-life
  configurable, measured via `eval --loto`.
- **Anti-match can punish generic places** → capped, off by default.
- **A larger pre-filter costs more popularity/climate calls** → opt-in.
