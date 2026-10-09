# Proposal

## Why

The recommendation catalog is GeoNames **municipalities**, so it suggests small
towns (e.g. *Torrevieja*) as if they were self-contained destinations. Travel is
better matched to **areas** — *Costa del Sol*, *Cinque Terre*, *Amalfi Coast* —
which Wikivoyage already models (Regions / Cities / Other destinations).

## What Changes

- Build the recommendation catalog from **Wikivoyage**, at region/area
  granularity, each Destination tagged with its granularity.
- **Narrow GeoNames to reverse-geocoding** visited trips (its real strength),
  kept as a catalog fallback only.
- Destinations carry a `granularity` field and a prose extract from Wikivoyage.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `destination-catalog`: candidates come from a travel catalog at area
  granularity (Wikivoyage), tagged by granularity; GeoNames is retained for
  offline reverse-geocoding of visited trips.

## Impact

- `wanderlens/catalog/wikivoyage.py` (new) — fetch/parse/build.
- `wanderlens/core/models.py` — `Destination.granularity`.
- `wanderlens/pipeline/recommend.py` / `evaluate.py` — default catalog source.
- `wanderlens/config.py` — catalog source.
