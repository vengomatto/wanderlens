# Roadmap

Deferred decisions, captured for the next phase. Not commitments — a parking lot.

## v2 — Preference Factors

- **Trip context** as a Preference Factor: season, companions, pace. (You travel
  with a toddler and minimise accommodation changes.) Requires data outside the
  photo archive, so it waits.
- **Explicit in-app feedback**: let the user rate/favourite Recommendations and
  feed that back into the Taste Profile. Needs a feedback surface; strong signal
  once the core loop works.

## v2 — Interface

- **Web app** — layered on the same core as the CLI.
- **Chat** — via the existing Telegram/nanobot setup, same core.

## v2 — Incremental ingestion (background)

- **Detect new photos automatically** — watch the archive (filesystem watcher or
  cheap poll) and ingest new/changed files without a manual `ingest`.
- **Run CLIP in the background** — embed new photos in a worker/queue and persist
  incrementally, so the CPU-heavy step never blocks the user.
- **Foreground stays fast** — `recommend` / `profile show` operate on whatever is
  already embedded; a normal run should feel like **10–30 s**, not minutes.
- Implications: a job queue, incremental DB writes, path-change invalidation, and
  a "profile is N photos behind" indicator.

## Cross-cutting — Open-source readiness

- v1 is single-user, but foundations must not assume it stays that way
  (see the multi-user foundation decision in the ADRs / session).

## Providers

- Destination descriptions come from an ordered provider chain. Implemented:
  `wikimedia` (Wikipedia/Wikidata), `openstreetmap` (free OSM features via
  Nominatim + Overpass, best-effort), and `llm` (OpenRouter, no search by
  default). Order is configurable. Next candidates: a curated local file.
- Attribute tags from the VLM are still freeform comma lists; move to structured
  extraction constrained to the shared vocabulary.

## Known limitations

- **Exclusion is by proximity** (default 60 km around each visited trip,
  `WANDERLENS_EXCLUDE_RADIUS_KM`), not by country. Geography is still only used
  to exclude; it is not yet a positive taste signal. The earlier idea of
  two-level country/region **weighting** (country 30 / region 70) is deferred
  until geography proves useful for ranking.
- **Country is a coarse proxy for culture.** What matters is the *vibe* of a
  place (captured today by attributes/embeddings). A future direction is to elicit
  explicit preferences — e.g. whether the user wants to **re-experience the same
  vibes** or seek *novelty* — and to model that orientation alongside the
  photo-derived taste.

- **Ranking blends attribute matching with faceted embeddings.** Taste is now a
  set of per-trip facets (scored by best match, not a global mean) and attribute
  weight is cross-trip recurrence. Coastal destinations still lead; the embedding
  term stays flat because destination text is thin. Next lever: richer destination
  attributes, and `alpha` tuning.
- **Trip splitting** is a fixed 18h / 150km heuristic; the Malta archive split
  into 2 trips over one overnight gap. Make thresholds configurable.
