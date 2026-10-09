# Design

## Context

See proposal.md — Why. v1 built the candidate catalog from GeoNames names only,
which starved ranking and made the hold-out evaluation uninformative. The
`destination-catalog` capability now needs Destinations to carry descriptive text.

Constraint discovered while designing: the Wikidata Query Service (SPARQL) is
heavily rate-limited from this host (HTTP 429/504). We must use request/response
APIs instead.

## Goals / Non-Goals

**Goals:**
- Give each candidate Destination a short description so CLIP text embeddings are
  meaningful.
- Fetch at most once per Destination; keep working offline afterwards.
- Never fail ranking because enrichment failed.

**Non-Goals:**
- Building a full tourist-attraction ontology or attribute taxonomy.
- Live enrichment at recommendation time (build-time/cached only).
- Fixing the CLIP model or tuning the taste vector.

## Decisions

**Wikimedia as the description source, via the action APIs, not WDQS.** Use the
Wikipedia `generator=search` intro extract (`"<name> <country>"`) as the primary,
richer description, and Wikidata `wbsearchentities` as a concise fallback.
*Alternatives:* Wikidata SPARQL (rejected: 429/504 from this host); per-QID REST
(rejected: we don't hold QIDs); no enrichment (rejected: leaves the core weakness).

**Country-qualified search for disambiguation.** Query `"<name> <country>"` and
take the top hit, which reliably resolves ambiguous names (e.g. Cartagena → the
Spanish city). *Alternatives:* title lookup (rejected: ambiguity, exact-title
mismatch).

**Enrichment is a distinct, cache-aware step.** Only records missing a description
are fetched; results persist in `data/catalog/destinations.json`. Subsequent runs
read the cache and make no network calls. *Alternatives:* enrich at import
(rejected: slow, non-offline).

**Graceful degradation.** Any fetch error leaves the record with an empty
description; ranking falls back to `name, country`.

## Risks / Trade-offs

- **Wikipedia title mismatches** → country-qualified search plus fallback to the
  Wikidata short description; a bad match degrades one candidate, not the run.
- **Build-time latency** (~one request per candidate) → cache makes it one-off;
  keep the candidate count bounded.
- **Rate limits** → polite delay and a descriptive User-Agent; enrichment is
  resumable because partial results are cached.
