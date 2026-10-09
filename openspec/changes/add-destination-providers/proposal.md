# Proposal

## Why

Destination descriptions are currently hard-wired to Wikimedia (Wikipedia /
Wikidata). That is one useful source, not the only one, and the choice of source
should be pluggable like Photo Sources are.

## What Changes

- Introduce a **Description Provider** port and a configurable provider chain.
- Make **Wikimedia** one provider and add a cheap **LLM provider** over OpenRouter
  (optionally search-grounded) as another.
- Enrichment tries providers in a configured order; the first non-empty
  description wins; results are cached as today.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `destination-catalog`: descriptions now come from a configurable provider chain
  rather than a single hard-wired source; Wikimedia is one provider among several.

## Impact

- `wanderlens/core/ports.py` — `DescriptionProvider` port.
- `wanderlens/catalog/providers.py` (new) — Wikimedia + LLM providers and chain.
- `wanderlens/catalog/fetch.py` — enrichment consumes providers.
- `wanderlens/config.py` — provider order / LLM model configuration.
