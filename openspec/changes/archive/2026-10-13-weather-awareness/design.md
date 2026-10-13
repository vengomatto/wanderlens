# Design

## Context

See `proposal.md`. `catalog/fetch.py:fetch_climate(lat, lon)` already returns a
12-month temperature/precipitation climatology from the keyless Open-Meteo
archive endpoint; guides store it. Trips in the DB carry `start_at`/`end_at` and
a `lat`/`lon`. Ranking accepts injectable signals (tags, popularity, feedback).
`core/` stays runtime-free; hosted/network calls are best-effort.

## Goals / Non-Goals

**Goals:** a cached, user-scoped climate preference from trips; a destination
climate match and best-months; an optional, off-by-default ranking bias and
season preference; weather visual attributes.

**Non-Goals:** no mandatory climate fetch; no change to default ranking; no
learned model; no weather in the core profile until data supports it.

## Decisions

### Pure climate logic in `core/climate.py`
`band(temp)` (cold/mild/warm/hot), `climate_profile(per_trip)` (mean temp, mean
precip, month weights), `best_months(monthly, profile)` (months within the
comfort band and below the destination's median precipitation), and
`climate_match(monthly, profile)` in [0,1] (temperature proximity plus
preferred-month overlap). Pure and deterministic, so it is unit-testable without
network.

### Trip weather in `catalog/climate.py`
`fetch_trip_weather(lat, lon, dates, session)` calls the Open-Meteo archive for the
trip's actual dates and aggregates mean temp/precip. Cached in a user-scoped
`trip_weather` table keyed by `(user_id, trip_id)`. The profile is derived from
cached rows and stored as `profile_entries` with `factor='climate'`.

### Destination climate cached in `destination_climate`
Reuse `fetch_climate(lat, lon)` for a Destination, cached catalog-scoped. In
`run_recommend`, compute the profile once, then for the **recommendations**
(best-effort) fetch/compute climate, best months, and match; store them.

### Ranking bias is opt-in
`rank_destinations(..., climate=None, climate_weight=0.0, season=None)` adds
`climate_weight * match` and, for a season, a small overlap bonus. Defaults are
`0.0`/`None`, so ranking is byte-identical without it. Only when enabled does
`run_recommend` fetch climate for the shortlist (bounded, cached).

*Alternative:* always fetch climate for all candidates — rejected; unbounded
network.

### Weather visual attributes
Add `weather` synonyms (clear sky, blue sky, cloudy, overcast, sunny, mist, fog,
rain, storm) to the shared vocabulary, feeding the existing attribute signal.

## Risks / Trade-offs

- **Noise from few trips / seasonality** → the bias is off by default, low weight
  when enabled, and measured via `eval --synthetic`.
- **Extra network** → only per trip (cached) and per recommended destination
  (cached, best-effort).
- **Crude comfort band** → simple and transparent; tunable later.

## Migration Plan

1. Additive `trip_weather` and `destination_climate` tables via `db`.
2. New steps best-effort; absent data changes nothing.
3. Rollback: ignore the tables and leave the weights at defaults.
