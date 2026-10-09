# Design

## Context

See proposal.md — Why. GeoNames is a place gazetteer (municipalities); Wikivoyage
is a *travel* hierarchy: each country page has `==Regions==`, `==Cities==`, and
`==Other destinations==` sections linking area-level articles.

## Goals / Non-Goals

**Goals:**
- Area-level candidates with coordinates + prose, free and keyless.
- A granularity tag per Destination.
- GeoNames kept solely for reverse-geocoding visited trips.

**Non-Goals:**
- A full Wikivoyage hierarchy walker (country-page sections are enough for v1).
- Popularity/novelty scoring (separate roadmap item).
- Live per-request fetching (built and cached).

## Decisions

**Parse country-page sections.** For each candidate country, fetch the page
wikitext and extract links under `Regions` / `Cities` / `Other destinations`,
tagging granularity from the section. Drop `File:`/image links. *Alternatives:*
category members (rejected: not populated for these lists).

**Batch-resolve details.** Resolve coordinates (`prop=coordinates`) and intro
extracts (`prop=extracts`) for ~20 titles per MediaWiki request; cache the built
catalog as JSON (`JsonCatalog`). Destinations without coordinates are skipped
(they cannot be ranked/excluded spatially).

**`Destination.granularity`.** A field: `region` | `city` | `other`. Section
membership is imperfect (a city can appear under Regions), so granularity is
recorded and can be filtered later rather than assumed.

**Source + fallback.** `config.catalog_source` (default `wikivoyage`); if the
travel catalog yields nothing for a country, fall back to the existing GeoNames
build. GeoNames reverse-geocoding is unchanged.

## Risks / Trade-offs

- **Section link noise / disambiguation** (e.g. "Valencia (region)") → keep the
  title as the name; coordinates disambiguate.
- **Wikivoyage API shape changes** → parsing is isolated in one module with
  mocked-session tests; failures fall back to GeoNames.
- **Coordinate coverage varies** → Destinations without coordinates are dropped,
  never ranked blindly.
