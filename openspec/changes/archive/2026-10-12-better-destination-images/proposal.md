# Proposal

## Why

Destination galleries are sourced by a **Commons geosearch radius**, which returns
whatever photos are geotagged nearby — flowers, ISS shots, random details. That is
the weakest part of the page. Curated place imagery (the encyclopedia article's
own media, the item's image, and the place's Commons **category**) is far more
relevant and needs no new infrastructure.

## What Changes

- Source a Destination's gallery from **curated place imagery**, in order:
  1. the item's image (Wikidata `P18`),
  2. the encyclopedia article's own images (`prop=images`),
  3. the place's **Commons category** (`P373`, name fallback).
- **Filter and rank** images: drop icons/logos/maps/flags/diagrams, low-resolution
  and unsupported formats; deduplicate; hero first.
- Keep the proximity geosearch gallery **only as a fallback** when curated sources
  yield too few images.
- Attribution/licence still recorded per image; the cache and schema are unchanged.
- No **BREAKING** changes.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `destination-media`: the gallery is drawn from curated place imagery
  (article media, item image, Commons category), filtered and deduplicated, with
  the proximity search used only as a fallback.

## Impact

- `wanderlens/catalog/fetch.py`: helpers for Wikidata `P18`, Wikipedia article
  images, Commons category members, and batched `imageinfo`, plus an image
  quality filter.
- `wanderlens/catalog/media.py`: `WikimediaMediaProvider` builds the gallery from
  the curated chain; `CommonsMediaProvider` becomes the fallback.
- Tests with fake Wikipedia/Wikidata/Commons responses for sourcing, filtering,
  deduplication, and fallback.
