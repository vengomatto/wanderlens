# Proposal

## Why

Visited places are excluded at **country** granularity, so one trip to Trentino
(Italy) removes every Italian destination — Sicily, Amalfi, the Dolomites
elsewhere — from consideration. That is too blunt for large countries.

## What Changes

- Record each trip's **location** (centroid lat/lon) on the trip.
- Exclude candidate Destinations by **proximity** to visited trips (a radius),
  not by country.
- Make the exclusion radius configurable.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `taste-profiling`: trips record their centroid location.
- `recommendation`: visited places are excluded by proximity, not country.

## Impact

- `wanderlens/db.py` — `trips.lat` / `trips.lon` (+ migration).
- `wanderlens/pipeline/profile.py` — store trip centroids.
- `wanderlens/core/recommend.py` + `pipeline/recommend.py` / `evaluate.py` —
  proximity filter.
- `wanderlens/config.py` — exclusion radius.
