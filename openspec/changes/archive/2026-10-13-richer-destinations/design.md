# Design

## Context

See `proposal.md` for motivation. Relevant current state:

- `core/gallery.py` already builds a deterministic in-memory fixture used only by
  `eval --synthetic`; it produces vectors and Destinations, not files on disk.
- `catalog/media.py` gathers Commons/Wikipedia/Wikidata images, filters by mime /
  width / blocklist, and downloads them; the provider chain is
  `WikimediaMediaProvider` then `CommonsMediaProvider`.
- `catalog/guide.py` gathers guide sections and stores itineraries from
  Wikivoyage links or a hosted `ItinerarySynthesizer` (needs a key).
- `models/` is the only place hosting HTTP model calls; `pipeline/enrichment.py`
  already caches model output in the user-scoped `taste_enrichment` table.
- No API key is configured in this environment, so all hosted steps currently
  fall back to deterministic behavior.

Constraints: `core/` imports no external runtime; hosted HTTP stays in `models/`;
persisted rows are user-scoped (catalog-scoped caches are allowed as with
`destination_popularity`); ranking stays deterministic; hosted steps are cached
and never fatal.

## Goals / Non-Goals

**Goals:**

- A broad, runnable synthetic dataset that exercises the whole pipeline.
- Higher-quality, openly-licensed imagery, with pluggable sources and legal
  external link-outs.
- Richer, scannable, optionally LLM-written destination descriptions.
- An itinerary that works with no key, plus travel-diary links.
- A sourced "case" for a destination that reads like an argument, not a list.

**Non-Goals:**

- No embedding of proprietary imagery (Getty et al.) — links only.
- No mandatory key: every hosted step is optional with a keyless fallback.
- No change to ranking's determinism or the ports/adapters boundaries.

## Decisions

### Materialise the synthetic archive to disk

Extend `core/gallery.py` with a data-only description of the mock archive and add
a materialiser (a dev/eval module) that writes EXIF-tagged JPEGs plus a
`destinations.json` catalog into a target directory, so the normal
`ingest → profile → recommend` path runs unchanged. The in-memory `Gallery`
stays as the eval fixture.

*Alternative:* seed the DB directly — rejected; it bypasses the real pipeline and
would not exercise ingestion.

### Quality tiers from Commons assessments

When gathering Commons files, request `extmetadata` (which carries categories)
and rank images whose page belongs to *Quality images*, *Featured pictures*, or
*Valued images* ahead of generic category images. Combine with a raised minimum
width, a landscape-aspect preference, and perceptual near-duplicate detection.

*Alternative:* a per-destination quality search query — rejected as brittle.

### Media sources behind a port

Add a `MediaSourceProvider` protocol (`fetch(destination) -> images`) in
`core/ports.py`. Keep Wikimedia/Commons as defaults; add optional Openverse /
Unsplash / Pexels providers enabled only when their key is configured. The
existing ordered provider chain and best-effort behavior are reused. External
searches (Getty, Google Images, Commons search) are added as **outbound links**,
never downloads.

### Case: keyless assembly, optional search + LLM

`catalog/case.py` assembles a case from Wikivoyage/Wikipedia/Wikidata/Commons
facts (a lead narrative plus citation links). `models/case.py` holds an optional
`HostedCaseWriter` that takes a `SearchProvider` (keyed: Tavily/Brave) and the
hosted text model, writing grounded prose. Results are cached in a user-scoped
`destination_case` table keyed by `(destination_id, input_hash, model,
prompt_version)`. No key → keyless case; error → keyless case; the run never
fails.

*Alternative:* require search — rejected; most users have no key and the keyless
case is already an improvement.

### Deterministic itinerary from POIs

Add `_poi_itinerary(pois, days)` that groups a destination's points of interest
into `days` ordered chunks (by existing order, balanced by count), producing
`{title, items}` days. Used when no synthesizer is configured; the LLM itinerary
still takes precedence when a key is present.

### Travel diaries and structured description

Gather diary links from the Wikivoyage page's external/"Go next" links plus a
configurable `travel_blogs` list (matched by place name), deduped. Structure each
description into a lead sentence plus highlight sentences for scannable display,
and let `taste-enrichment`/case enrichment replace the prose when a key exists.

## Risks / Trade-offs

- **Legal exposure from proprietary images** → only embed openly-licensed files;
  link out for the rest.
- **Cost/latency of search + LLM** → cached by input+model+prompt, capped,
  keyless fallback; never fatal.
- **Fixture size (many JPEGs)** → write small solid-color images with EXIF; keep
  the generator parameterised and out of the main `data/` tree.
- **Quality assessment false positives** → tiering only reorders; existing
  filters still apply.
- **New tables/columns** → additive migration; catalog-scoped for destination
  data, user-scoped for per-user cases.

## Migration Plan

1. Additive `destination_case` table and a `diaries` column on `destination_guide`
   via `db`.
2. New steps are best-effort; existing guides/media are untouched and render as
   before until `guide --refresh` / `recommend` rebuild them.
3. Rollback: ignore the new table/column and the new providers; nothing else
   changes.

## Open Questions

- Default search provider (Tavily vs Brave vs SerpAPI) and default blog list —
  configurable, not load-bearing.
- Exact quality-tier ordering and near-duplicate threshold — tuned at
  implementation.
