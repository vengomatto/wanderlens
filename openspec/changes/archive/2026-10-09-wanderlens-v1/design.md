# Design

## Context

See proposal.md — Why. Greenfield project; constraints that shape the approach:

- Target host is Raspberry-Pi class: CPU-only, ~3 GB free disk, no GPU. Local
  model work must be modest and batched.
- The only available archive today is a 90-photo Malta trip (GPS + EXIF intact)
  copied to `data/photos/`. The loop must be provable on this thin data.
- Existing credentials for hosted vision models (OpenRouter/Anthropic) are
  available on the host.
- The app is single-user now but must not foreclose a public multi-user release.

Requirements live in `specs/`; this document covers only how they are met.

## Goals / Non-Goals

**Goals:**
- A CLI proof of the full loop: ingest → profile → recommend → eval, on real photos.
- Recognition owned by Wanderlens (data-model-agnostic), swappable models.
- Persisted state scoped by user id from day one.
- Runs on the Pi host with no GPU and no photo-manager dependency.

**Non-Goals:**
- Multi-user auth, accounts, or a hosted service.
- An Immich (or other manager) adapter — deferred to the roadmap.
- Incremental/streaming ingestion — batch is sufficient for v1.
- Web or chat interfaces — CLI only.
- Trip-context and explicit-feedback Preference Factors — parked in `docs/ROADMAP.md`.

## Decisions

**Ports & adapters, folder as the reference Photo Source.** The `core/` never
imports a photo manager; sources implement one port. *Alternatives:* Immich as a
hard dependency (rejected: an adoption wall for an open-source app and couples
our differentiator to another product's schema); Immich-plugin-only (rejected:
fails the open-source goal). Recorded in `docs/adr/0001`.

**Hybrid recognition: local embeddings + sampled hosted VLM.** Compute CLIP/SigLIP
embeddings locally on every photo (cheap, private, scales), and call a hosted
vision LLM on a representative sample for attribute tags and explanations.
*Alternatives:* reuse Immich's CLIP (rejected: portability + we own recognition);
all-VLM tagging (rejected: cost and privacy across a whole archive); all-local VLM
(deferred: quality/CPU trade-off, and it can slot behind the same seam later).

**Hybrid recommendation: embedding shortlist → LLM re-rank.** Embed candidate
Destination descriptions, score against the Taste Profile embeddings for a
shortlist, then let the LLM rank the final few and write the explanations from the
user's photos. *Alternatives:* pure rule scoring (rejected: brittle vocabulary);
pure LLM ranking over the full catalog (rejected: unbounded, unreproducible).

**Python.** Best first-class support for EXIF, geo, CLIP runtimes, and SQLite.
*Alternatives:* TypeScript (weaker ML ecosystem); Rust/Go (slower to iterate for
a data/ML-heavy tool).

**SQLite, user-scoped, no auth.** A single-file DB keeps v1 trivial on the Pi and
migrates cleanly to Postgres later; a `user` id threads through every record now.
*Alternatives:* Postgres + pgvector immediately (rejected: operational weight for
one user); single-user schema (rejected: painful later migration). Recorded in
`docs/adr/0002`.

**External catalog: Wikidata + GeoNames, offline geo naming.** Wikidata (CC0) as
canonical Destinations, GeoNames for offline name resolution. *Alternatives:*
LLM-generated destinations (rejected: ungrounded, unreproducible); a hand-kept
seed list (allowed as a fixture for `eval`, not as the catalog).

**Batch pipeline, one `ingest` run over the whole archive.** Trivial to re-run and
reason about while the pipeline is still wrong. *Alternatives:* incremental
(deferred to v2).

**Hold-out evaluation.** Temporarily remove a visited place from the profile and
check whether the system re-recommends it. *Alternatives:* a labelled yes/no set
(deferred: more effort than the thin archive justifies); no eval (rejected: no
signal we are learning anything).

**Module layout.** `core/` (taste + recommendation, no external imports),
`sources/` (folder adapter behind the port), `catalog/`, `models/` (embeddings,
VLM), `pipeline/`, `cli/`. The Immich-free core is what makes the open-source
story real and keeps the model seam swappable.

## Risks / Trade-offs

- **Thin archive (90 photos, one trip) yields a weak, overfit profile** →
  treat v1 numbers as smoke tests, not quality claims; grow the archive before
  tuning; keep the hold-out check honest.
- **CPU-only embeddings are slow** → batch, downscale inputs, and cache vectors;
  embeddings are one-time per photo.
- **Hosted VLM cost and privacy** → sample only representative photos per trip;
  never send the full archive.
- **VLM tag vocabulary vs. catalog attribute vocabulary mismatch** → define one
  shared attribute vocabulary both sides map into, so matching is meaningful.
- **GPS clustering / geocoding inaccuracy** → offline GeoNames with a manual
  override path later; a mislabelled trip degrades gracefully.
- **External catalog coverage and rate limits** → cache responses locally; the
  catalog is bulk-fetched, not queried per recommendation.
- **Disk headroom (~3 GB)** → photos, vectors, and DB share one small volume;
  downscale where quality allows and monitor growth.

## Migration Plan

Greenfield: no data migration. Provisioning order: (1) Python env + deps;
(2) copy GeoNames data and the photo folder into `data/`; (3) run `ingest` to
build the DB; (4) `profile show` and `recommend` to validate; (5) `eval` as the
quality gate. Rollback is deleting `data/` and re-running `ingest` — no remote
state.

## Open Questions

- Exact embedding model and dimensionality (e.g. SigLIP vs OpenCLIP variant) —
  swappable behind `models/`.
- Vector storage: `sqlite-vec` extension vs. brute-force over a small archive.
- Precise trip-splitting thresholds (time gap and spatial jump).
- Whether `eval` needs a fixture catalogue to make held-out places resurface
  predictably.
