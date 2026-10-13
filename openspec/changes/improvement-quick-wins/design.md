# Design

## Context

See `docs/IMPROVEMENT_PLAN.md` for the full analysis and `proposal.md` for scope.
`models/embeddings.py:111` truncates text ids to 77 and pads, dropping CLIP's end
token. `core/evaluate.py` only resurfaced a single held-out trip. `popularity`
uses `log10(views)/6` with fixed 0.33/0.66 thresholds. `pipeline/profile.py:99`
embeds photos without error handling. `pipeline/recommend.py` builds cases for the
shortlist; `catalog/fetch.py` extracts keep `==` headings.

## Decisions

### CLIP end token
`_encode_text` truncates to `CONTEXT_LENGTH - 1` and re-appends the end token id
(49407) before zero-padding, so CLIP pools at the end token for any length. Add a
`cache_key` property (`clip-vit-base-patch32-textv2`) and have
`ensure_destination_embeddings` key the cache by `cache_key` so old collapsed
vectors recompute; vision (photo) embeddings are unaffected. Regression test uses
a pure `_truncate_with_eos` helper with different long id lists.

### Percentile popularity
`percentile_labels(scores)` ranks the pool's scores and returns famous for the top
third, uncommon for the bottom third, balanced otherwise; `rank_destinations`
uses it when popularity is present, falling back to the absolute label. The
persisted `popularity_label` therefore reflects the pool.

### Leave-one-trip-out harness
`core/evaluate.py` gains `mean_reciprocal_rank`, `recall_at_k`, and a
`loto_evaluate` that, per trip, reuses the existing `run_eval` machinery to obtain
a ranked list and records the first near destination. `pipeline/evaluate.py`
gains `run_loto` returning the metrics; `run_eval` stays. `scripts/eval.sh` runs
it and compares MRR to a `docs/eval-baseline.json`.

### Diagnostics
`rank_destinations` can return components; `recommend --diagnose` prints the std
of embedding/attribute/score across the pool, the share of destination vectors
that are near-identical (cosine > 0.99 to another), and the top-20 attribute and
country mix. Implemented as a small function over the returned recommendations
and cached vectors.

### Small fixes
- Strip `== ... ==` lines and collapse whitespace in `fetch_wikipedia_media`'s
  extract; sentence-aware cut in `_truncate`.
- `_embed_photos` wraps each photo in try/except, counting failures.
- Cases built for `recommendations` (final N), not `shortlist`.

## Risks / Trade-offs

- **Percentile needs a pool** → falls back to the absolute label when the pool is
  tiny.
- **Changing the cache key forces a one-time recompute** → acceptable, once.
- **LOTO over few trips is noisy** → it reports averages and a margin, not a
  gate on a single trip.
