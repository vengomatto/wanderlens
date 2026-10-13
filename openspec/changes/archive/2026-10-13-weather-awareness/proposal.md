# Proposal

## Why

Taste is built from geography, subjects, and aesthetics, but never from the
weather the user actually travelled in — even though we already fetch climate for
destinations. Adding a climate signal lets the app say what weather someone likes
and when a destination suits them, and feeds recommendations.

## What Changes

- **Trip climate profile.** Derive each trip's weather from free historical data
  (Open-Meteo archive, keyless) using its coordinates and dates, cache it, and
  aggregate a user climate preference (temperature band, precipitation, preferred
  months) into the Taste Profile.
- **Destination climate match.** Compute each destination's monthly climate
  (cached), its **best months for you**, and a climate-match score, and surface
  them on the destination page.
- **Optional ranking signal.** A configurable, low-weight climate term and a
  `--season` preference can bias ranking; both are **off by default** so ranking
  stays as-is until tuned.
- **Weather visual attributes.** Add sky/weather terms (clear sky, overcast,
  cloudy, sunny, mist, rain) so the vision/enrichment path captures the weather
  the user shoots.
- No **BREAKING** changes; all new steps are best-effort and cached.

## Capabilities

### New Capabilities
- `trip-climate`: derives a trip's weather and a user's climate preference from
  free historical data, cached and user-scoped.

### Modified Capabilities
- `recommendation`: an optional climate-match bias and a season preference.
- `destination-guide`: destination climate is cached with best-months and a match
  score relative to the user's climate preference.
- `web-interface`: the destination page shows best months and the climate match.

## Impact

- New `wanderlens/core/climate.py` (pure: bands, profile, best months, match) and
  `wanderlens/catalog/climate.py` (Open-Meteo fetch for trips).
- `wanderlens/catalog/fetch.py`: a historical trip-weather fetch (reuses the
  Open-Meteo archive endpoint already used for climatology).
- `wanderlens/core/vocabulary.py`: weather terms.
- `db.py`: `trip_weather` (user-scoped) and `destination_climate` (catalog-scoped)
  tables.
- `wanderlens/pipeline/recommend.py`: build the climate profile and (when enabled)
  pass a climate bias / season.
- `wanderlens/web/`: show best months and the climate match.
- New tests for the profile, bands, best months, match, and the optional bias.
