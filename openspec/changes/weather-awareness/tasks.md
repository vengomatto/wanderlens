# Tasks

## 1. Pure climate logic

- [ ] 1.1 Add `core/climate.py` with temperature bands, `climate_profile`, `best_months`, and `climate_match`; verify deterministic unit tests for bands, profile shape, best months, and match bounds.
- [ ] 1.2 Add weather terms (clear sky, overcast, cloudy, sunny, mist, fog, rain) to `core/vocabulary.py`; verify a vocabulary test.

## 2. Trip weather and profile

- [ ] 2.1 Add `fetch_trip_weather` (Open-Meteo archive for a trip's dates) and a user-scoped `trip_weather` table; verify a test with a fake session and a cache test.
- [ ] 2.2 Build and store the climate preference (`profile_entries` factor `climate`) from cached trip weather in `run_recommend`; verify a test that a profile is built and that missing data is tolerated.

## 3. Destination climate match and display

- [ ] 3.1 Add a catalog-scoped `destination_climate` table and compute/cache monthly climate for recommendations; compute best months and match; verify a test with an injected climate fetcher.
- [ ] 3.2 Show best months and the climate match on the destination page from cache only; verify a `TestClient` render shows them and omits them when absent.

## 4. Optional ranking signal

- [ ] 4.1 Add `climate`/`climate_weight`/`season` to `rank_destinations` (defaults off); verify a test that the bias reorders otherwise-equal candidates and that defaults leave ranking unchanged.
- [ ] 4.2 Wire `--season` / `WANDERLENS_CLIMATE_WEIGHT` through config and the recommend pipeline so the shortlist climate is fetched only when enabled; verify CLI parsing and that it is off by default.

## 5. Documentation and verification

- [ ] 5.1 Update `README.md` for the trip climate profile, best months, and the optional season/climate weight; verify the documented commands run.
- [ ] 5.2 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
