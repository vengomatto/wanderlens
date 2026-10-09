# Proposal

## Why

The Taste Profile is a single mean over every photo. With more trips it flattens
toward "generic travel photo", and a large album (89 Malta shots) drowns out a
small one (4 Trentino shots). Subject weights are aggregated per tag occurrence,
which rewards big albums rather than genuinely repeated preferences.

## What Changes

- Keep a **taste facet per trip** (a per-trip embedding centroid) and score a
  Destination by its **best-matching facet** (max), so distinct tastes (coastal,
  alpine) coexist instead of averaging away.
- Weight each canonical attribute by **how many trips contain it**, not how many
  photos or tags — weight = distinct-trips / total-trips.
- Store subjects per trip so recurrence can be computed.
- Cover trips equally regardless of album size.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `taste-profiling`: subjects are stored per trip; attribute weights come from
  cross-trip recurrence; taste is a set of per-trip facets.
- `recommendation`: ranking scores against the best-matching taste facet.

## Impact

- `wanderlens/db.py` — `trip_subjects` table.
- `wanderlens/pipeline/profile.py` — per-trip tag storage, recurrence weights.
- `wanderlens/core/recommend.py` + `pipeline/recommend.py` / `evaluate.py` —
  faceted embedding scoring.
