# Tasks

## 1. Wikivoyage module

- [x] 1.1 Add `catalog/wikivoyage.py`: parse a country page's `Regions` / `Cities` / `Other destinations` sections, batch-resolve coordinates + extracts, and build Destinations with a granularity tag. Verify: mocked-session tests parse a sample page and build area-level Destinations.

## 2. Model

- [x] 2.1 Add `Destination.granularity` and include it in serialization/normalization. Verify: a round-trip test preserves granularity.

## 3. Catalog wiring

- [x] 3.1 Build the default catalog from Wikivoyage (cached), falling back to GeoNames when empty; add `catalog_source` config; use it in `recommend` and `eval`. Verify: a test uses Wikivoyage when available and falls back when not.

## 4. Integration & docs

- [x] 4.1 Build the real catalog and run `recommend`; confirm area-level destinations (e.g. Costa del Sol, Cinque Terre) appear and GeoNames still reverse-geocodes trips. Update docs.
