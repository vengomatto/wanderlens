# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (F1): the deterministic itinerary splits points of
interest by their existing order, so a day can bounce across the map. Grouping by
geography keeps a day in one area — which matters for the "few accommodation
changes" goal.

## What Changes

- **Geographic day grouping.** The POI-based itinerary groups points of interest
  into days by proximity (a greedy nearest-neighbour route), falling back to the
  simple split when coordinates are missing.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `destination-guide`: the deterministic itinerary groups POIs by geography.

## Impact

- `wanderlens/catalog/guide.py`.
- Tests with positioned points of interest.
