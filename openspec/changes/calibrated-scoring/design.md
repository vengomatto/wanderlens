# Design

## Context

See `proposal.md`. `rank_destinations` computes `alpha * embedding_score +
(1 - alpha) * attribute_score` plus small bias deltas. Embedding is a compressed
cosine (~0.27); the attribute sum can exceed 1. `_select` uses the last tuple
element as the vector for MMR, so any new field must not become the last element.

## Decisions

### Calibrate over the scored pool
The loop now records `base` (the `alpha`/`1-alpha` combination) and `delta` (the
novelty/feedback/climate/season bias) separately, with the vector kept as the last
tuple element so MMR is unaffected. When `calibrate=True`, `_calibrate` min-max
rescales the embedding and attribute columns across the pool and recomputes
`base` from the rescaled terms, then adds `delta`. Degenerate pools (all equal)
normalise to 0. Off by default, per the plan's "measure first" rule.

### Exact-title pageviews
`article_title(destination)` returns `destination.id[3:]` for `wv:` ids and the
display name otherwise; `fetch_popularity_for` uses it for the pageviews lookup.

## Risks / Trade-offs

- **Calibration can compress a real gap** (it made near-duplicates look closer in
  a spike), which is why it is opt-in and gated on `eval --loto`.
- **`wd:` ids carry no title** → they still use the name; the QID-keyed lookup is
  a later step (B1).
- **Recency/engagement trip weighting and the anti-match penalty (also A3)** are
  not in this change — they need their own metric gate.
