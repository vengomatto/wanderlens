# Design

## Context

See proposal.md — Why. The profile's embedding is `mean(all photo embeddings)`
and its subjects are tag counts; both scale with album size and flatten with more
trips.

## Goals / Non-Goals

**Goals:**
- Preserve distinct tastes as trips accumulate (no averaging to mush).
- Make attribute weight reflect *repeated across trips*, not album size.
- Keep ranking deterministic and cheap (no new models, no training).

**Non-Goals:**
- Learning weights from feedback.
- Clustering facets (k-means) — per-trip facets are enough for now.
- Two-level geography / proximity exclusion (separate change).

## Decisions

**Taste = one facet per trip.** For each trip, average its photo embeddings into
a centroid and normalize. The profile is the set of facets, not their mean.
*Rationale:* a coastal trip and an alpine trip both remain visible. *Alternatives:*
single mean (rejected: flattens); k-means over trips (deferred).

**Score a destination by its best-matching facet.** `embedding_score =
max_f dot(facet_f, destination)`. A destination that strongly matches *any* taste
scores high. *Rationale:* avoids averaging away strong but narrow preferences.

**Attribute weight = cross-trip recurrence.** For each canonical attribute,
`weight = (# trips containing it) / (# trips)`. Stored per trip in
`trip_subjects`. *Rationale:* recurrence is preference; album size is not. A trip
contributes its attribute set once regardless of photo count.

**Per-trip tagging already samples ~3 photos**, so each trip is represented by a
bounded, comparable sample before recurrence is computed.

## Risks / Trade-offs

- **Max-pooling over-favours one dominant facet** → acceptable; it is a real
  preference. Tune later with top-k averaging if needed.
- **Trips are the unit** → a mis-split trip skews one facet; trip splitting is a
  known limitation (see roadmap).
- **Facet count grows with trips** → linear and small; ranking is O(trips ×
  destinations).
