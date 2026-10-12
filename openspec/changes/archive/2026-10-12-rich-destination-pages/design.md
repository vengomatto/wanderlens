# Design

## Context

See `proposal.md` for motivation; `specs/destination-media/spec.md` and
`specs/web-interface/spec.md` for the behavior contracts.

Current state that shapes the approach:

- The dashboard (archived `add-web-dashboard`) reads only SQLite and renders
  offline; a static test forbids heavy model imports outside `wanderlens/models/`.
- `catalog/providers.py` already implements an ordered, best-effort Description
  Provider chain (`wikimedia → openstreetmap → llm`) with a keyless Nominatim
  helper and a `OSM_USER_AGENT`. `catalog/fetch.py` holds the Wikipedia/Wikidata
  HTTP helpers.
- `destination_embeddings` is a **catalog-scoped** (non user-scoped) table;
  `photo_embeddings` and trip facets are already cached, so taste similarity can
  be computed without the model runtime.
- `run_recommend` already persists destination display fields and score
  components; media is the missing piece for a rich page.

## Goals / Non-Goals

**Goals:**

- Rich destination pages rendered entirely from local cache, keeping the web
  layer read-only and offline.
- Attributable, license-aware media from free keyless sources.
- An honest region highlight: precise when possible, approximate and labelled
  otherwise.

**Non-Goals:**

- No user photo upload, no favourites/feedback (still read-only).
- No paid/image-search APIs; no scraping.
- No on-the-fly fetching at page render; no per-request external calls.
- No exact-boundary guarantee for informal areas (only honest approximation).

## Decisions

### Fetch media during `recommend`, cache it, render from cache

Media (images, long extract, region geometry) is fetched inside
`run_recommend` for the returned Recommendations, using the same best-effort,
idempotent pattern as the description chain. The web layer reads the cache only.

*Alternatives:* a separate `enrich` command (extra manual step) or lazy
fetch-on-first-view (breaks offline/read-only). Rejected in favour of the
seamless cached-during-recommend option; a `--no-media` flag keeps `recommend`
usable without network.

### Catalog-scoped cache tables plus files on disk

Two additive tables, mirroring `destination_embeddings`:

- `destination_media(destination_id PK, title, page_url, extract, source,
  license, attribution, region_geojson, region_kind, region_radius_km,
  fetched_at)`
- `destination_images(destination_id, position, filename, source, license,
  attribution, PK(destination_id, position))`

Image bytes are written under `data/media/{destination_id}/{position}.jpg`
(git-ignored). Negative results are also recorded (empty rows / a `fetched_at`
marker) so a miss is not retried every run. Non-user-scoped because it is shared
catalog data, exactly like `destination_embeddings`.

### A media provider chain, like descriptions

`catalog/media.py` orchestrates an ordered chain in the spirit of
`build_provider_chain`:

1. `WikimediumProvider` — Wikipedia page image (`pageimages`/`page/summary`) for
   the hero, plus a long extract by title.
2. `CommonsGalleryProvider` — Wikimedia Commons geosearch near the coordinates
   for a small gallery.
3. Region resolver — see below.

A `DestinationMediaProvider` Protocol is added to `core/ports.py` (Protocol only;
no runtime import). Every step is best-effort: a miss or error falls through and
never fails the run.

### Region geometry: precise polygon, else sized circle

Resolution chain (`catalog/media.py` / `catalog/regions.py`):

1. If the Destination id is a Wikidata entity (`wd:Q…`), resolve `P402` (OSM
   relation) and fetch its boundary.
2. Otherwise (and as fallback) query Nominatim with `polygon_geojson=1` for
   `name, country` and take the first polygon/multipolygon.
3. Otherwise store an approximate circle: a GeoJSON point with a radius sized to
   `granularity` (region ≈ 40 km, other ≈ 20 km, city ≈ 10 km), and set
   `region_kind = "approximate"`.

Precise polygons are simplified before storage to keep the page payload small.
`region_kind` (`precise` / `approximate`) is persisted so the UI can label the
overlay honestly. Coordinates absent → no geometry.

*Alternatives:* Wikidata geoshapes only (sparse coverage), Overpass boundary
search (noisy). Rejected; the chain maximises coverage while staying precise when
it can.

### Destination detail page and dual maps

A `/destinations/{id}` route renders from `destination_media` +
`destination_images` + the persisted Recommendation row. It shows a hero image,
the expanded extract with source link and attribution, a "why this is for you"
card (explanation + score components), and **two Leaflet maps**: a world locator
(pinned, whole-world view) and a regional map that draws the region geometry as
a GeoJSON layer (polygon or circle) with an "approximate" note when applicable.
GeoJSON is embedded via `tojson`.

Basemap is **Carto Positron / Dark Matter** (keyless, keyed to
`prefers-color-scheme`), with "© OpenStreetMap contributors © CARTO" attribution
— a cleaner look than default OSM.

### Similar-visit evidence without the model runtime

`web/views.py` gains `similar_trips(conn, user_id, destination_id)`: it reads the
cached `destination_embeddings` vector for the destination and the per-trip
facets from `photo_embeddings`, ranks trips by cosine similarity (numpy only),
and returns the top trips with a few of their photo ids. No model is loaded, so
the existing "render without the model runtime" requirement still holds.

### Visual polish

Image-first Recommendation cards with an SVG **radial score gauge** and
component bars; hero images with gradient scrim and attribution; CSS
**View Transitions** for htmx-boosted navigation; **skeleton loaders** and
hover/motion refinements; refined typography and dark-mode palette. These are
presentation-only and change no data.

### Thumbnail/media serving stays local and scoped

Image files are served through a route that resolves the filename from
`destination_images` (never a client-supplied path); the user's photos continue
to be served through the existing user-scoped photo route. No destination media
route leaks filesystem paths.

## Risks / Trade-offs

- **Coverage is uneven** (obscure areas lack images/polygons) → graceful
  placeholders, circle fallback, and "approximate" labelling; the page is useful
  without media.
- **Licensing/attribution** → only free sources (Wikipedia/Commons), with source
  and license stored and shown.
- **Nominatim/Overpass rate limits and ToS** → reuse the existing UA and delay,
  one request per destination, cached so it happens at most once.
- **Large polygons bloat pages** → simplify before storing; cap point counts.
- **Media fetch slows `recommend`** → best-effort with timeouts, `--no-media`
  opt-out, and idempotent caching.
- **Model runtime creeping into the web layer** → similar-visits uses cached
  vectors only; the existing static import test and the subprocess render test
  still guard this.

## Migration Plan

1. Additive `CREATE TABLE` for `destination_media` / `destination_images` in the
   schema (idempotent; no migration of existing data needed).
2. Ship the media chain and the `recommend` integration; a run without network
   or with `--no-media` simply leaves pages media-less.
3. Rollback: dropping the web routes and the media tables leaves the CLI, schema,
   and existing pages untouched.

## Open Questions

- Default gallery size (propose 4 images) and hero resolution — cosmetic.
- Polygon simplification tolerance and per-granularity circle radii — tune at
  implementation; does not change the approach or specs.
