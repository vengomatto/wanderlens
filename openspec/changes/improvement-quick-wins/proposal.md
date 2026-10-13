# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (Sonnet): recommendations are weak mostly because
of pre-ranking data defects, not weights. This change lands the plan's Phase 0–1
"quick wins": the evaluation harness needed to judge anything, the CLIP
truncation fix, the popularity percentile, and a few small pipeline fixes.

## What Changes

- **Evaluation harness (A0).** Leave-one-trip-out evaluation over all trips,
  reporting MRR / Recall@10 / Recall@50 (not a single pass/fail), a
  `recommend --diagnose` score breakdown (per-component spread, collapsed-vector
  share, top-20 attribute/country mix), and a `scripts/eval.sh` regression gate.
- **Fix CLIP text truncation (L1).** Re-append the end token after truncation and
  bump the destination-embedding cache key so collapsed vectors recompute.
- **Popularity percentile (A5.1).** Label famous/balanced/uncommon by percentile
  within the catalog instead of an absolute pageview scale.
- **Pipeline quick wins.** Strip wikitext headings from extracts (B5), make the
  description cut sentence-aware (A1.2), tolerate an unreadable photo in
  `_embed_photos` (L15), and build cases only for the final recommendations, not
  the whole shortlist (C4.1).
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `evaluation`: leave-one-trip-out metrics and score diagnostics.
- `recommendation`: the embedding signal no longer collapses on long text.
- `destination-popularity`: percentile-based classification.
- `destination-media`: clean, sentence-aware extracts (headings stripped).
- `destination-case`: cases built for the final recommendations only.
- `taste-profiling`: unreadable photos do not abort profiling.

## Impact

- `wanderlens/models/embeddings.py`, `pipeline/recommend.py`,
  `core/evaluate.py`, `pipeline/evaluate.py`, `catalog/popularity.py`,
  `catalog/fetch.py`, `catalog/case.py`, `pipeline/profile.py`, `cli/main.py`,
  `scripts/eval.sh`.
