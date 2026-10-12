# Proposal

## Why

The dashboard (archived `add-web-dashboard`) shows Recommendations as text-only
cards: a name, a one-line description, a score, and a generic explanation. It
does not convey *what a place looks like* or *where in the world it is*, which is
most of the appeal of travel discovery. This change adds pictures, a real
destination page with a long description and locate-on-the-world maps, and a
more polished visual language — so the app feels like a travel product rather
than a debug view.

## What Changes

- **Pictures and long descriptions** for each Destination, fetched from free
  Wikimedia/Wikipedia/Commons sources, with source link, license, and
  attribution, and cached locally so the dashboard stays offline and read-only.
- **A destination detail page** (`/destinations/{id}`): hero image, expanded
  description, "why this is for you", facts, and a link to the source article.
- **Locate on maps**: a world locator plus a regional map that highlights the
  destination's area — a precise polygon when one exists, otherwise an
  approximate sized circle, always labelled as such.
- **"You loved places like this"**: the user's own trip photos whose taste is
  closest to the destination, shown as evidence.
- **Visual polish**: image-first recommendation cards with a radial score gauge,
  a modern keyless basemap (Carto Positron/Dark Matter), view transitions,
  skeleton loaders, and refined typography/dark mode.
- Media is fetched during `wanderlens recommend` (cached), so the web layer
  still never calls out at render time. Additive, no **BREAKING** changes.

## Capabilities

### New Capabilities
- `destination-media`: retrieves and caches a Destination's images, expanded
  description, source/attribution, and region geometry from free sources, so a
  rich page can be rendered offline.

### Modified Capabilities
- `web-interface`: Recommendation cards gain a picture and a link to a new
  destination detail page; new requirements cover the detail page, the
  locate-on-the-world maps with region highlight, and similar-visit evidence.

## Impact

- `wanderlens/core/ports.py`: a `DestinationMediaProvider` port (Protocol only).
- `wanderlens/catalog/`: a media provider chain (Wikimedia page image +
  Commons gallery + long extract) and a region-geometry resolver (Wikidata/OSM
  polygon → Nominatim polygon → sized circle).
- `wanderlens/db.py`: two additive, catalog-scoped tables `destination_media`
  and `destination_images` (like `destination_embeddings`, not user-scoped).
- `wanderlens/pipeline/recommend.py`: fetch and cache media for the returned
  recommendations (best-effort, idempotent); a `--no-media` CLI flag to opt out.
- `wanderlens/web/`: a `/destinations/{id}` route, a local media route, dual
  maps with GeoJSON overlay, radial gauge, similar-trips view, and CSS/motion.
- `data/media/` (git-ignored) for cached image bytes.
- New tests for the media provider chain, region fallback, persistence, and the
  new pages.
