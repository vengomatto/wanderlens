# Design

## Context

See `proposal.md`. `core/taste.py:haversine_km` gives distances; `Destination`
has coordinates. Ranking already accepts a `season`. Persistence is user-scoped
(ADR 0002). The web shell posts forms via HTMX.

## Decisions

### A single-row brief per user
`traveller_brief(user_id PRIMARY KEY, adults, children, pace, season,
max_travel_km, home_lat, home_lon, budget, updated_at)`. `pipeline/brief.py`
provides `save_brief(conn, user_id, **fields)` (upsert only the given fields) and
`load_brief(conn, user_id) -> dict`. Missing/None fields mean "not set".

### Applied in the pipeline, not the core
`run_recommend` loads the brief and, when `home_lat/lon` and `max_travel_km` are
present, filters candidates with `haversine_km`; the brief's `season` is used when
no explicit season is set. The core ranker is unchanged (no new required input).

### CLI and panel
`wanderlens brief [--adults … --home LAT,LON …]` sets fields and `brief` (or
`--show`) prints them. The taste page shows a brief form posting to `/brief`,
which saves and redirects.

## Risks / Trade-offs

- **Travel time is approximated by distance** (no airport dataset yet) → labelled
  as a maximum distance; a flight-time model is a later step (B3).
- **Budget/family effects need price/profile data** → stored, applied best-effort
  only where the data exists; never fatal.
