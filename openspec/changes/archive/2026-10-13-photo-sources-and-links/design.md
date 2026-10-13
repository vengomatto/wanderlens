# Design

## Context

See `proposal.md`. `catalog/media.py` already has an `ImageSourceProvider`-style
seam (`OpenverseMediaProvider.images()` used as an *extra source* on
`WikimediaMediaProvider`), and `build_media_chain(session, sources)` adds
Openverse only when `"openverse"` appears in `sources`. `web/views.py` has
`external_photo_links(name, country)` used only on the destination page.

## Decisions

### Enable Openverse by default, add keyed providers
Default `media_sources` becomes `["openverse"]`. Add `UnsplashMediaProvider` and
`PexelsMediaProvider` (both returning the common image-dict shape) and register
them in `build_media_chain` when their key is present. Keys come from config
(`WANDERLENS_UNSPLASH_KEY`, `WANDERLENS_PEXELS_KEY`); `build_media_chain` takes a
`keys` mapping so it stays testable. All extra sources are merged into the
Wikimedia provider's curated list and pass through the same filter/dedupe.

*Alternative:* scrape Getty — rejected; unlicensed and against their ToS.

### Photo links on the card and a dedicated section
Reuse `external_photo_links` for the card (`RecView.photo_links`) and move the
destination-page links into their own section, so they are visible without a
case.

## Risks / Trade-offs

- **Extra network per destination** → best-effort, filtered, cached; failures
  ignored; no proprietary embedding.
- **Keyed providers need keys** → disabled unless configured; documented.
