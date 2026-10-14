# Design

## Context

See `proposal.md`. `catalog/guide.py:_poi_itinerary(pois, days)` chunks points by
their list order into roughly equal days. POIs carry `lat`/`lon` when parsed from
the travel guide. `core/taste.haversine_km` gives distances.

## Decisions

### Greedy nearest-neighbour days
`_cluster_pois(pois, days)` keeps located points, targets
`ceil(len/days)` per day, seeds each day with the next unassigned point, and
greedily appends the nearest remaining point until the day is full. Points without
coordinates attach to the last day. Deterministic (stable ordering of the input).
`_poi_itinerary` uses the clusters when any located points exist, otherwise the
previous equal split.

## Risks / Trade-offs

- **Greedy is not optimal** → good enough and deterministic; a k-means/route
  optimisation is a later step.
- **Few points** → falls back gracefully.
