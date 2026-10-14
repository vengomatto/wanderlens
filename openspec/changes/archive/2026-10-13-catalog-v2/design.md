# Design

## Context

See `proposal.md`. `catalog/wikivoyage.py:country_destination_titles` regexes
every `[[link]]` inside a section body, so prose mentions leak in and
first-section-wins mis-tags granularity. `build_country_destinations` drops
places without coordinates but keeps everything else; ids are `wv:<title>` with
no QID. `catalog/regions.py` only uses Wikidata P402 for `wd:` ids.

## Decisions

### Identity on the Destination
Add `wikidata_id` to `Destination` (and to serialization). `build_country_destinations`
sets it from the page's `pageprops.wikibase_item`. Media and region lookups pass
it through so they can use the item image/Commons category and P402 rather than a
name search; the id stays `wv:<title>` for compatibility (no re-keying).

### Section-aware parsing and templates
`country_destination_titles` is rewritten to read a section body as *entries*:
top-level list items (`* [[Title]]`) and `{{marker|...}}`, `{{listing|...}}`,
`{{Regionlist|...}}` templates. Link targets are normalised (strip `#`/`|`), and
targets equal to the parent country or to any known country name are dropped.
Granularity comes from the section. A `parse_section_entries(wikitext, section)`
helper returns `(title, granularity, lat, lon, qid)` where the template provides
coordinates/QID directly, avoiding a second API call.

### Quality gate and coverage
`build_wikivoyage_catalog`/`build_country_destinations` accept
`min_extract_chars` (default 0 = off) and log drops; `countries` becomes a config
value so the pool can extend globally. Defaults stay as today so nothing regresses.

## Risks / Trade-offs

- **Template variety is wide** → parse the common `marker`/`listing`/`Regionlist`
  shapes and keep the `[[link]]` path as a fallback; unknown templates are ignored.
- **Global coverage is slow** → it is opt-in via config; the plan itself stages a
  pilot.
- **QID lookups change network behaviour** → best-effort and cached as before.
