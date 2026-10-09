# Tasks

## 1. Trip location

- [x] 1.1 Add `trips.lat` / `trips.lon` (with migration) and store the centroid of each trip's geotagged photos. Verify: a test stores a centroid for a geotagged trip and none for an unlocated one.

## 2. Proximity exclusion

- [x] 2.1 Add a haversine proximity filter and use it in `run_recommend` instead of country exclusion; add `exclude_radius_km` to config. Verify: a far, same-country destination stays eligible while a nearby one is excluded.

## 3. Evaluation

- [x] 3.1 Rework `run_eval` to hold out a trip (by city), recompute facets/attributes without it, exclude near the remaining trips, and report whether a destination near the held-out centroid resurfaces. Verify: a test holds out a trip and reports a resurfacing result.

## 4. Integration & docs

- [x] 4.1 Re-run `recommend` on the archive and confirm Italian destinations far from Trentino are now eligible; update docs.
