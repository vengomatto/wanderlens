# Tasks

## 1. Providers

- [x] 1.1 Add a `DescriptionProvider` port in `core/ports.py` and a `catalog/providers.py` with `WikimediaProvider` (wrapping the existing fetch functions) and `LlmProvider` (OpenRouter chat, search-capable model). Verify: tests with mocked sessions assert each provider parses a description and returns `None` on a miss.
- [x] 1.2 Add a provider chain used by `enrich_records`, honoring a configured order and falling back on empty/error. Verify: tests show first-provider-wins, fallback on failure, and that adding a provider needs no caller change.

## 2. Config & integration

- [x] 2.1 Add `description_providers` (ordered) to config and build the chain from it. Verify: a test builds the default chain and an overridden one.
- [x] 2.2 Integration: enrich a couple of places through the real LLM provider and confirm a description is returned and cached. Verify: a real call yields a non-empty sentence; the cache prevents a second call.

## 3. Docs

- [x] 3.1 Update `README.md` / `docs/ROADMAP.md` to describe the provider chain and the LLM option. Verify: docs name the providers and how to configure the order.
