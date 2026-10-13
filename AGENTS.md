# AGENTS.md

## Commands

- Run tests: `.venv/bin/python -m pytest -q`
- End-to-end smoke: `bash scripts/smoke.sh`
- Synthetic ranking quality: `.venv/bin/python -m wanderlens eval --synthetic`
- Runnable mock archive: `.venv/bin/python -m wanderlens synthetic --dir /tmp/wl-syn`
- CLI: `.venv/bin/python -m wanderlens <ingest|profile show|recommend|eval|serve|guide|synthetic>`
- Web dashboard (local, read-only): `.venv/bin/python -m wanderlens serve`

## Conventions

- **Ports & adapters.** `wanderlens/core/` must not import external runtimes or
  any photo manager. New backends (photo sources, catalogs, models) implement a
  port from `core/ports.py`.
- **Model runtime is confined to `wanderlens/models/`.** `onnxruntime`,
  `tokenizers`, `torch`, `open_clip`, and VLM HTTP calls live only there. A test
  enforces this.
- **Everything persisted is user-scoped.** New tables/rows carry a `user_id`
  (see `core/db.py` / `docs/adr/0002`).
- **Hosted model steps are cached and never fatal.** Enrichment/synthesis calls
  are injectable, cached by input + model + prompt, and fall back to the local
  deterministic result; they must not fail the run.
- **Determinism.** Ranking must be repeatable for identical inputs; the LLM
  re-ranker is optional and injectable.

## Layout

`core/` taste + recommendation · `sources/` photo sources · `catalog/` place
data · `models/` embeddings + vision · `pipeline/` stages · `cli/` entry point.

Planning lives in `openspec/`; the v1 change and specs are in
`openspec/changes/wanderlens-v1/`.
