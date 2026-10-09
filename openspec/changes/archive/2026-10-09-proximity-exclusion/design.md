# Design

## Context

See proposal.md — Why. Exclusion is `exclude_countries`, which over-removes for
large countries. Trips already resolve to a city/country but do not store
coordinates.

## Goals / Non-Goals

**Goals:**
- Exclude only the *area* visited, not the whole country.
- Tunable radius; deterministic.

**Non-Goals:**
- Geographic similarity as a positive taste signal (deferred).
- Admin-region taxonomy (not needed for a radius rule).

## Decisions

**Store a trip centroid.** Mean lat/lon of the trip's geotagged photos, on
`trips.lat`/`trips.lon`. Added via a `PRAGMA table_info` check + `ALTER TABLE` so
existing DBs migrate.

**Exclude by haversine radius.** A candidate is dropped when its distance to any
visited trip centroid is ≤ `exclude_radius_km` (default 60 km). This keeps
far-away destinations in the same country eligible. *Alternatives:* country
exclusion (rejected: too blunt); admin-region membership (rejected: needs extra
data for no clear gain).

**Configurable.** `exclude_radius_km` in config/env.

**Eval holds out a trip.** Build facets and attribute recurrence *without* the
held-out trip, exclude near the remaining trips, then check whether a destination
near the held-out centroid resurfaces.

## Risks / Trade-offs

- **Radius too small/big** → configurable; 60 km is a sensible default for
  "you've been here".
- **Sparse coordinates** → GeoNames destinations carry lat/lon, so coverage is
  good; trips without geotagged photos simply contribute no exclusion.
- **Overlapping trips** → multiple centroids are all applied; a destination near
  any of them is excluded.
