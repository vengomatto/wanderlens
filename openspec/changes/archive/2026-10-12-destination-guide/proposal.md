# Proposal

## Why

The destination page (archived `rich-destination-pages`) shows a hero image, one
paragraph, and a map. That is enough to be curious, not enough to **prepare a
trip**: a traveller wants a rich, travel-oriented description, books to read
before going, a real photo gallery, useful links, the points of interest on the
map, when to go, films set there, similar destinations — and a suggested
itinerary. Almost all of this exists in free, keyless sources we already touch
(Wikivoyage, Wikimedia, Wikidata); only the synthesised itinerary needs an LLM.

## What Changes

- Add a **`wanderlens guide` command** that builds and caches a rich guide for
  the recommended Destinations, outside the web request path.
- **Richer description**: the expanded prose now comes from **Wikivoyage**
  (travel-oriented *Understand*), with Wikipedia as fallback.
- **Photo gallery** of at least ten images where available (Commons + article
  media), with per-image attribution.
- **Reading list**: novels set in the destination (Wikidata `P840` narrative
  location) plus Open Library place/subject search.
- **Resource links**: ~10 deduplicated links (official site, Wikivoyage,
  Wikipedia, Commons category, OSM, tourism portals).
- **Points of interest** from Wikivoyage *See/Do* listings, plotted on the
  regional map.
- **When to go**: monthly temperature and precipitation from Open-Meteo.
- **Films and series set there** (Wikidata `P840`).
- **Similar destinations** from the catalog, by embedding similarity.
- **Suggested itineraries**: Wikivoyage's curated itineraries, plus an optional,
  **search-grounded LLM** day-by-day itinerary that is cached, marked as
  AI-generated, JSON-constrained, cites its sources, and never fails the run.
- All guide content is cached; the web layer stays read-only and offline. No
  **BREAKING** changes.

## Capabilities

### New Capabilities
- `destination-guide`: gathers and caches a Destination's travel-guide content —
  rich prose, links, books, points of interest, climate, films, and itineraries —
  from free sources plus an optional, cached, search-grounded LLM itinerary.

### Modified Capabilities
- `destination-media`: the gallery grows to at least ten images where available,
  and the expanded description is sourced from a travel guide (Wikivoyage) in
  addition to the encyclopedia.
- `web-interface`: the destination page gains the new guide sections (gallery,
  reading list, resource links, points of interest, when to go, films, similar
  destinations, suggested itineraries).

## Impact

- `wanderlens/catalog/`: a guide orchestrator and providers (Wikivoyage
  sections/listings, Wikidata books/films/links, Open Library, Open-Meteo), the
  gallery size increase in `media.py`.
- `wanderlens/models/`: the only place allowed to hold LLM HTTP; the injected
  itinerary model (pinned model + prompt, optional).
- `wanderlens/db.py`: additive, catalog-scoped `destination_guide` table (JSON
  columns) and `destination_itineraries` table.
- `wanderlens/cli/`: a `guide` subcommand (`--refresh`, `--no-llm`).
- `wanderlens/web/`: view models + templates/CSS/JS for the new sections and POI
  markers; similar destinations from cached embeddings.
- `wanderlens/config.py`: guide/LLM settings (model, search on/off, opt-out).
- New tests for providers, caching, the `guide` command, and the new page
  sections; no external calls at render.
