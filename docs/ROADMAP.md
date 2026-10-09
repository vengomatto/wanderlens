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

## Known limitations (from v1 build)

- **Destination text is thin.** The GeoNames catalog supplies only a
  `Name, Country` string, so recommendation and evaluation match on almost no
  signal. The first held-out evaluation did not resurface Malta. Enrich
  Destinations with Wikidata descriptions/tags before trusting ranking quality.
- **Trip splitting** is a fixed 18h / 150km heuristic; the Malta archive split
  into 2 trips over one overnight gap. Make thresholds configurable.
