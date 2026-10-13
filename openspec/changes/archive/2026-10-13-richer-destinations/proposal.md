# Proposal

## Why

Recommendations are too thin to feel convincing. The candidate pool comes only
from the small real catalog, photos are of variable quality, destination
descriptions are raw Wikipedia/Wikivoyage extracts, there are no itineraries, no
travel-diary links, and the hosted-model path is never exercised without a key.
The result does not make a *case* for a place. This change makes each
recommendation a rich, sourced destination story, and gives us a broad, runnable
dataset so all of it can be tested without the owner's few photos.

## What Changes

- **Runnable synthetic archive.** A deterministic generator writes a mock photo
  archive (trips with coordinates, dates, and attributes) plus a matching
  candidate catalog to disk, so `ingest → profile → recommend` can be exercised
  end-to-end on a broad dataset — not just the eval fixture.
- **Quality-tiered destination media.** Prefer Wikimedia Commons *Quality /
  Featured / Valued* images, raise the resolution floor, prefer landscape
  aspect, and dedupe near-duplicates. Media sources become **provider ports**
  (Commons; optional Openverse / Unsplash / Pexels when configured). Embed only
  openly-licensed images; **link out** to external photo searches (e.g. Getty,
  Google Images) without embedding their files.
- **Compelling, structured descriptions.** A destination's description is
  rendered as a scannable story (lead sentence + highlights) rather than a wall
  of extract, and is enriched by the hosted model when available.
- **Deterministic itineraries (no key).** Build a day-by-day itinerary from the
  destination's own points of interest when no model key is present; keep the
  Wikivoyage and LLM itineraries as richer alternatives.
- **Travel-diary and resource links.** Surface curated, license-safe travel
  diaries / journals / guides (Wikivoyage "Go next"/external links, and a
  configurable blog list) alongside the existing links.
- **A built case for each destination.** Assemble a strong, cited case for a new
  destination from keyless sources (Wikivoyage / Wikipedia / Wikidata / Commons),
  optionally augmented by a **web-search + LLM** step that writes a captivating
  description; cached by input + model + prompt, injectable, never fatal.
- No **BREAKING** changes; every hosted step degrades to the keyless result.

## Capabilities

### New Capabilities
- `synthetic-archive`: a deterministic mock photo archive and catalog on disk so
  the full pipeline can be run and evaluated on a broad dataset.
- `destination-case`: builds a sourced, compelling case (narrative + citation
  links) for a recommended destination, keyless by default and web-search + LLM
  enriched when configured.

### Modified Capabilities
- `destination-media`: quality-tiered, openly-licensed image sourcing through
  provider ports, with external link-outs and no embedded proprietary images.
- `destination-guide`: deterministic POI-based itineraries; travel-diary and
  resource links; structured, enriched description.
- `web-interface`: render the case, diary links, and the richer description and
  itinerary formatting.

## Impact

- `wanderlens/core/gallery.py`: extend the deterministic generator to emit a
  runnable archive (photos + catalog) under a target directory.
- `wanderlens/catalog/media.py` and `core/ports.py`: quality-tiered filtering,
  a media-source port, and optional Openverse/Unsplash/Pexels providers.
- `wanderlens/catalog/guide.py` / `pipeline/guide.py`: POI-based itinerary
  builder, diary-link gathering, structured description.
- New `wanderlens/catalog/case.py` (or `pipeline/case.py`) + a hosted
  web-search/LLM seam in `wanderlens/models/`; a cached `destination_case` table
  (user-scoped) and additive columns/table via `db`.
- `wanderlens/web/`: templates and view models for the case, diaries, and
  formatted sections.
- New tests for the generator, media filtering/tiers, itinerary building, diary
  links, and the case cache/fallback.
