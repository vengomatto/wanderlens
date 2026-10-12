# Design

## Context

See `proposal.md`; behavior is in `specs/destination-guide/spec.md`,
`specs/destination-media/spec.md`, and `specs/web-interface/spec.md`.

Current state that shapes the approach:

- `destination-media` (archived) caches a hero image, one extract, and a region
  geometry, fetched during `recommend` via a best-effort provider chain
  (`catalog/media.py`) and served read-only by `wanderlens/web/`.
- The description provider chain (`catalog/providers.py`) and
  `catalog/fetch.py` already talk to Wikipedia/Wikidata/Nominatim with a shared
  `USER_AGENT`; `models/` is the only place allowed to make LLM HTTP calls.
- The destination page already renders images, a description, dual maps,
  similar trips, and the evidence-based "why".

## Goals / Non-Goals

**Goals:**

- A trip-preparation page whose content is grounded in **free, keyless** sources,
  cached, and rendered offline.
- Keep the paid LLM to a single, optional, cached, source-citing itinerary.
- One `guide` command builds the guide; the web never calls out.

**Non-Goals:**

- No scraping (TripAdvisor/Google/blogs).
- No LLM-generated facts about books/links/POIs — those come from structured
  sources; the LLM only synthesises an itinerary from gathered POIs.
- No traveller-context questionnaire or multi-day planner UI (later changes).

## Decisions

### Wikivoyage is the backbone

Wikivoyage gives travel-oriented prose (*Understand*), section listings
(*See/Do/Eat/Sleep*), external links (*Go next*), and curated itineraries — all
keyless. We fetch the page's plaintext extract for the rich description, parse
listing templates for points of interest, and read its links. Wikipedia/Wikidata
remain fallbacks and supplements.

### A dedicated `guide` command

`wanderlens guide [--count N] [--refresh] [--no-llm]` builds guides for the
current recommended Destinations, idempotently, and caches them. It is separate
from `recommend` so the latter stays fast; like media, the guide is never built
in the request path.

### Catalog-scoped cache tables

- `destination_guide(destination_id PK, understand, links, books, pois, climate,
  films, fetched_at)` with JSON columns.
- `destination_itineraries(destination_id, position, title, summary, days, source,
  model, prompt_version, fetched_at, PK(destination_id, position))`.

Both are non-user-scoped, like `destination_embeddings` and `destination_media`;
a row (even partial) marks the destination as fetched so misses are not retried.

### Free sources per section

- **Rich prose**: Wikivoyage plaintext (`catalog/fetch.py`), Wikipedia fallback.
- **Gallery ≥10**: Commons geosearch with a higher `limit`, plus article media,
  deduplicated; images still cached by `media.py`.
- **Books** (Wikidata `P840` narrative location over works) + **Open Library**
  place/subject search.
- **Links**: Wikidata `P856` official site, Wikivoyage, Wikipedia, Commons
  category, OSM relation, tourism portals; deduplicated.
- **POIs**: Wikivoyage `see`/`do` listing templates (`name`, `lat`, `long`),
  parsed from wikitext; coordinates kept where present.
- **Climate**: Open-Meteo historical API at the destination's coordinates,
  aggregated to a per-month temperature and precipitation summary.
- **Films/series**: Wikidata `P840` over audiovisual works.

All wrapped in the existing best-effort pattern: a miss or error omits a section
and never fails the run. Ids for Wikidata are resolved from the Wikivoyage/
Wikipedia page's `wikibase_item` (via `pageprops`).

### Optional LLM itinerary

An `ItinerarySynthesizer` port (in `core/ports.py`) is injected; the default
lives in `models/` and uses `HostedTextModel` with a **pinned model and prompt
version**. It receives only the gathered POIs, the destination, the season, and
(if available) the traveller context, and must return JSON (a list of days). It
is opt-in, **search-grounded** where configured (`:online`) — the README's cost
note applies — and **cached** per `(destination_id, evidence fingerprint,
model, prompt_version)`. Any failure omits the synthetic itinerary and keeps the
curated ones; the run never fails.

### Similar destinations are computed, not fetched

`web/views.py` ranks other recommended Destinations by cached
`destination_embeddings` (numpy only) and returns the closest few. No model, no
network.

## Risks / Trade-offs

- **LLM cost/hallucination** → opt-in, cached, JSON-constrained, grounded in
  gathered POIs with sources; curated itineraries always available.
- **Wikivoyage wikitext parsing is fragile** → parse defensively, unit-tested
  against fixtures; a parse miss just omits POIs.
- **Open-Meteo/Nominatim/Overpass rate limits** → one request per destination,
  reused `USER_AGENT`, cached once.
- **Coverage gaps** → each section is independent and omitted when empty; the
  page degrades gracefully.
- **Attribution** → official-site/Wikivoyage/Wikimedia sources and licences are
  carried with links and images.

## Migration Plan

1. Additive `CREATE TABLE` for `destination_guide` and
   `destination_itineraries` (idempotent).
2. Ship `guide` and the page sections; a run without network simply leaves the
   page as it is today.
3. Rollback: dropping the command, tables, and sections leaves media, ranking,
   and the CLI untouched.

## Open Questions

- Gallery cap (propose 15) and POI cap (propose ~30) — tune at implementation.
- Itinerary length (propose 3–5 days) and whether to ask traveller context now
  or wait for the dedicated change — deferrable; does not change the approach.
