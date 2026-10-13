# Proposal

## Why

The current ranking is dominated by a single, coarse signal. On real archives the
embedding term is nearly flat across destinations (`0.266`–`0.278`) while
`attribute_score` decides almost everything, so half the score (`alpha=0.5`) is
spent on a dead signal. Two root causes: thin, tag-free destination text, and
taste facets that are unreliable when a trip has one or two photos — a
"trip centroid" built on one photo is just that photo. Attribute matching also
uses substring tests (`"art" in "earth"`), producing false positives. None of
this is measurable today because there is no quality metric and the only archive
is a handful of tiny trips.

## What Changes

- **Robust trip facets.** A trip contributes a facet only when it has enough
  photos; below the threshold the facet is weighted down (or omitted) so a
  one-photo trip no longer masquerades as a robust centroid.
- **Configurable trip splitting.** The capture-time gap and spatial jump that
  separate trips become explicit, configurable parameters rather than fixed
  18h/150km constants, so a real trip is not fragmented into two.
- **Correct, smarter attribute matching.** Canonical matching uses word
  boundaries instead of substrings, and matches are weighted by **specificity
  (IDF)** in addition to recurrence, so rare, informative attributes count for
  more than generic ones.
- **Unlock the embedding term.** A **hosted cheap model** becomes a first-class,
  cached enrichment stage in the pipeline (not a fallback): it turns a trip's
  flat tags into structured per-trip attributes, and expands thin destination
  text into a richer description used for embedding. Deterministic output is
  preserved (cache keyed by input + model + prompt; a local fallback when the
  model is unavailable) and the run never fails on model error.
- **Recalibrated blending.** With a live embedding signal the blend weight moves
  off `0.5` to a calibrated default, and per-facet embeddings are normalized so
  no facet dominates by magnitude.
- **A synthetic evaluation gallery.** A reproducible fixture mocks a photo
  gallery with known trips and attributes, and new metrics (`precision@k`, `MRR`)
  score the ranking against it — so every change above is measurable without
  more real data.
- No **BREAKING** changes; the deterministic core remains the default and CLI
  behavior is preserved.

## Capabilities

### New Capabilities
- `taste-enrichment`: a hosted cheap model, invoked as an injectable and cached
  stage of the profile/recommendation chain, that derives structured per-trip
  attributes and a richer destination representation, with a deterministic local
  fallback; it never fails the run.

### Modified Capabilities
- `taste-profiling`: trip splitting becomes configurable; taste facets are
  robust to trips with too few photos.
- `recommendation`: attribute matching uses word boundaries and specificity
  weighting; the embedding blend is recalibrated; the embedding signal is fed a
  richer destination representation.
- `evaluation`: adds a synthetic gallery fixture and precision@k / MRR metrics
  alongside the existing hold-out check.

## Impact

- `wanderlens/core/taste.py`: configurable split windows; robust facet weighting.
- `wanderlens/core/vocabulary.py`: word-boundary matching; expanded vocabulary;
  IDF helper.
- `wanderlens/core/recommend.py`: specificity-weighted attribute score;
  recalibrated `alpha`; per-facet normalization.
- `wanderlens/models/`: a structured-attribution / text-enrichment seam
  (hosted-model HTTP stays confined to `models/`).
- `wanderlens/pipeline/`: wire the enrichment stage (injectable, best-effort)
  into ingest/recommend; new config for split windows and the enrichment model.
- `wanderlens/core/evaluate.py` and fixtures: synthetic gallery, precision@k, MRR.
- `wanderlens/db.py`: any additive columns for structured attributes (user-scoped).
- New tests for word-boundary matching, IDF weighting, robust facets, the
  enrichment cache/fallback, and the metrics.
