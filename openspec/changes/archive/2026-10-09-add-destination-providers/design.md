# Design

## Context

See proposal.md — Why. Descriptions come from `default_description` in
`catalog/fetch.py`, which only knows Wikipedia/Wikidata. We want interchangeable
providers, with a cheap search-capable LLM as a second one.

## Goals / Non-Goals

**Goals:**
- A `DescriptionProvider` port with Wikimedia and LLM implementations.
- Configurable provider order; first non-empty description wins.
- Cache-aware and offline-safe as today.

**Non-Goals:**
- Many providers now (just enough to prove the seam).
- Changing ranking or the taste profile.
- Using the LLM to judge/rank — providers only produce text.

## Decisions

**Port shape.** `DescriptionProvider` exposes `name: str` and
`describe(name, country) -> str | None`. Providers never raise for a miss; they
return `None` so the chain can continue.

**Chain, ordered, first non-empty wins.** `enrich_records` walks the providers in
order, catching exceptions and empty results. Default order
`[wikimedia, llm]` — try the free source first, fall back to the paid one.
*Alternatives:* LLM-first (better coverage, costs more) — available by config.

**LLM provider on OpenRouter, search-grounded.** A single chat completion to a
cheap model, default `openai/gpt-4o-mini:online` (the `:online` suffix enables
web search on OpenRouter). The prompt asks for one factual sentence suitable for
matching travel taste. Only the place name and country are sent — never user
photos. *Alternatives:* Perplexity Sonar (native search; also fine, swappable via
the model string); plain completion without search (cheaper, less grounded).

**Config, not code, selects providers.** `config.description_providers`
(default `["wikimedia", "llm"]`) and `config.vlm_model` for the LLM slug.

## Risks / Trade-offs

- **LLM cost** → only place names are sent, results are cached, and Wikimedia
  runs first so the LLM is a fallback.
- **Hallucination** → search grounding plus Wikimedia-first; a vague description
  degrades one candidate, never the run.
- **Search variability** → the provider returns the model's sentence; if it looks
  unusable the destination falls back to `name, country` at ranking time.
