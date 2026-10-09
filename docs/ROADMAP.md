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

- **Ranking now uses attribute matching** over the shared vocabulary, blended
  with embeddings (`alpha`, default 0.5). Coastal Taste Profile now ranks coastal
  cities first; inland Rivas-Vaciamadrid fell from rank 5 to 44, Puente de
  Vallecas from 1 to 65, and the held-out Malta evaluation still passes (rank 3).
  Still worth tuning `alpha` and moving from one global taste mean to per-trip
  centroids.
- **Trip splitting** is a fixed 18h / 150km heuristic; the Malta archive split
  into 2 trips over one overnight gap. Make thresholds configurable.
