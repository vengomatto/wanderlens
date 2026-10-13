# Design

## Context

See `proposal.md`. Current state: `catalog/destinations.py:normalize_record` builds
Destinations with raw names and no granularity for some sources;
`catalog/media.py:fetch_media` short-circuits on `is_media_cached` and dedupes by
title only; there is no feedback table; `catalog/case.py` builds cases only for
final recommendations; `models/ranker.py:HostedItinerarySynthesizer` uses POIs
only; `synthetic.py:materialize` writes photos+catalog but no tags. Ranking already
accepts injected signals (`taste_tags`, `popularity`, `diversity`).

Constraints: core stays runtime-free, hosted calls stay in `models/`, ranking is
deterministic, persisted rows are user-scoped, new steps never fatal.

## Goals / Non-Goals

**Goals:** clean/narrow-free catalog; refreshed, deduped media; a feedback signal
that changes ranking; the case visible where the choice is made; grounded
itineraries and default diaries; a synthetic archive that exercises attributes.

**Non-Goals:** no learned model, no change to the ports boundaries, no mandatory
network, no change to exclusion.

## Decisions

### Catalog hygiene as a normalization pass
Add `clean_destination(destination)` (strip a trailing parenthetical qualifier,
collapse whitespace, title-case while preserving all-caps acronyms) and
`dedupe(destinations)` by `(clean_name.lower(), country.lower())`; assign
granularity from a bounded set `{city, region, area}`. Apply when a `JsonCatalog`
is constructed from records and when loaded. Widen `DEFAULT_CANDIDATE_COUNTRIES`
to more European codes.

*Alternative:* edit the source data — rejected; normalization belongs in code and
keeps external data replaceable.

### Media refresh and perceptual dedupe
`fetch_media(..., refresh=False)`: with `refresh`, ignore the cache and rebuild
(clear images). Compute a 64-bit average hash of each downloaded image with PIL;
skip an image whose hash is within a small Hamming distance of one already kept.
`--refresh-media` and `WANDERLENS_REFRESH_MEDIA` expose it.

### Feedback table and a deterministic bias
`feedback(user_id, destination_id, action, created_at, PK(user_id,
destination_id))`. `action ∈ {save, like, dislike, skip}`. Ranking takes
`feedback: dict[str, str]` and adds `+w` for like/save, `-w` for dislike/skip
(`w` small, configurable), leaving order unchanged when empty. CLI
`wanderlens feedback --destination <id> --action ...`, listing and clearing; web
buttons post to a route that writes the row.

### Shortlist cases and card surfacing
Build cases for the shortlist before final ranking (best-effort, cached), and
have `recommendations_view` include a case snippet from `destination_case` on the
`RecView`, rendered on the card.

### Grounded itinerary and default diaries
Thread an optional `searcher` into `gather_guide`; when present, pass its results
to `HostedItinerarySynthesizer.synthesize(destination, pois, days, search_results)`
(prompt includes them). Keep the keyless POI itinerary fallback. Add a small
default `travel_blogs` list.

### Synthetic tags
`materialize` also writes `subjects.json` (trip index -> canonical attributes per
cluster), and the `synthetic` command seeds the profile's subjects from it after
ingest, so attribute matching is exercised without a vision model.

## Risks / Trade-offs

- **Feedback gaming / cold start** → small weight, no hard filters, deterministic
  when absent.
- **Refresh cost** → explicit flag; default stays cached.
- **Perceptual hash false positives** → only reorders/drops within a Destination
  gallery; conservative threshold.
- **Name normalization losing meaning** → keep the parenthetical-cleaned name only
  for display; ids are unchanged.
- **Wider countries / heavier catalog build** → cached as before.

## Migration Plan

1. Additive `feedback` table via `db`.
2. Catalog normalization applies on next catalog build; existing cache is
   normalized on load, so no migration needed.
3. Rollback: drop the feedback table and ignore the flags; nothing else changes.
