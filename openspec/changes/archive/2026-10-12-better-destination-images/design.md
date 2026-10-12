# Design

## Context

`destination-media` currently builds the gallery from `fetch_commons_gallery`
(geosearch by radius) plus the article's single page image. The page image is
good; the radius gallery is noisy. Wikipedia/Wikidata already give us the title
and the `wikibase_item` (used by `destination-guide` for `P840`), so curated
sources are reachable with the same session and no new infrastructure.

## Goals / Non-Goals

**Goals:**

- Relevant, licensed, deduplicated photographs, at least ten where available.
- Keep the provider chain, cache, schema, and offline rendering unchanged.

**Non-Goals:**

- No new paid/stock providers, no scraping.
- No change to image storage, thumbnailing, or serving.

## Decisions

### Source chain: item image → article media → Commons category

For a Destination:

1. **Item image**: Wikidata `P18` on the `wikibase_item` (the canonical hero).
2. **Article media**: the encyclopedia article's own files via
   `action=query&prop=images&titles=…`, then batched `imageinfo`.
3. **Commons category**: Wikidata `P373` (fallback: the Destination name) via
   `generator=categorymembers&gcmtype=file`, then batched `imageinfo`.

The hero is the `P18` image, otherwise the article's page image; the gallery is
the merged, filtered, deduplicated list. The travel-theme is unchanged (the
article's images already reflect the place, unlike a radius search).

### Batched imageinfo and a quality filter

A single helper resolves file titles → `imageinfo`
(`url|size|mime|extmetadata`, `iiurlwidth=1280`). Candidates are kept only if:

- mime is `image/jpeg`, `image/png`, or `image/webp` (no SVG);
- width ≥ 800 px;
- the title does not match a blocklist (icon, logo, map, flag, coat of arms,
  diagram, chart, symbol, banner, emblem, locator, commons/edit UI);
- not already seen (dedupe by file title).

The gallery is capped (~15) and starts with the hero.

### Proximity search only as fallback

If the curated gallery yields fewer than a threshold (propose 4) and the
Destination has coordinates, append `fetch_commons_gallery` (geosearch) results,
filtered by the same rules. Otherwise the proximity service is not called.

### Behaviour preserved

`WikimediaMediaProvider` still returns a single `DestinationMedia` (extract,
hero, gallery); `CommonsMediaProvider` remains the fallback provider.
`catalog/media.py`'s download/cache path is untouched, so attribution, negative
caching, and offline reuse are unchanged.

## Risks / Trade-offs

- **Wikidata/`P373` coverage varies** → name-based category fallback; if a
  category is missing, the article media still populates the gallery.
- **Category members can include non-photographic files** → the quality filter
  and blocklist handle most; the cap and dedupe limit noise.
- **More API calls per destination** (article images + category + imageinfo) →
  batched, cached once, and still keyless; the run stays best-effort.
- **Filter over-blocking** → thresholds are constants; tune if galleries come out
  too small, and the geosearch fallback still fills them.

## Open Questions

- Exact minimum width (800 px) and the blocklist terms — tune at implementation.
- Cap (15) and fallback threshold (4) — cosmetic, do not change the approach.
