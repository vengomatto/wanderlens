# Proposal

## Why

A personal photo archive is a rich, already-paid-for record of where someone
travels and what they love about it, yet it does nothing for planning the next
trip. Wanderlens turns that archive into personalized recommendations for *new*
destinations, and is built from the start as a portable, open-source tool rather
than a locked-in plugin.

## What Changes

- Introduce **Wanderlens**, a single-user Python CLI that learns a travel
  **Taste Profile** from a **Photo Archive** and recommends new **Destinations**.
- Read photos from a **local folder** (the v1 reference **Photo Source**); a
  photo-manager adapter (Immich) is deliberately deferred.
- Run our own recognition pipeline: local CLIP/SigLIP **embeddings** over every
  photo, plus a hosted vision-LLM on a **sample** for human-readable attribute
  tags and explanations.
- Derive visited geography by clustering photos into **trips** (time + GPS) and
  reverse-geocoding them.
- Source candidate Destinations from an external place catalog (Wikidata +
  GeoNames).
- Rank Destinations against the Taste Profile (embeddings shortlist → LLM
  re-rank) and explain each Recommendation using the user's own photos.
- Persist everything in **SQLite**, every record scoped by a `user` id (no auth in
  v1), to keep a clean path to the later public multi-user app.
- Expose a CLI: `ingest`, `profile show`, `recommend`, `eval`.

## Capabilities

### New Capabilities

- `photo-ingestion`: reading a Photo Archive through a Photo Source port
  (local-folder adapter) and extracting per-photo metadata (timestamp, GPS,
  dimensions).
- `taste-profiling`: building the Taste Profile — trip clustering, reverse
  geocoding, embeddings, vision-LLM attribute tagging — and persisting it.
- `destination-catalog`: sourcing candidate Destinations from external place data
  and normalizing them into Destination records.
- `recommendation`: ranking Destinations against the Taste Profile and producing
  explained Recommendations.
- `evaluation`: the hold-out check that a visited Destination is re-recommended,
  used as the v1 quality signal.

### Modified Capabilities

- None (greenfield).

## Impact

- **New code**: a Python package with a photo-source-agnostic `core/`, plus
  `sources/`, `catalog/`, `models/`, `pipeline/`, and `cli/` modules.
- **Dependencies**: Pillow/exifread (image + EXIF), an open CLIP/SigLIP runtime
  (`open_clip`/`transformers`), reverse-geocoding data (GeoNames), HTTP client.
- **External services**: a vision LLM for tagging/explanation (existing
  OpenRouter/Anthropic credentials).
- **Storage**: local SQLite database and the photo folder (`data/`, git-ignored).
- **Constraints**: runs on a Raspberry-Pi-class host (CPU-only, ~3 GB free),
  which bounds archive size and forces the host-side model split (local
  embeddings, hosted VLM).
