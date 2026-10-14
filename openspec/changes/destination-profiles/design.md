# Design

## Context

See `proposal.md`. `taste-enrichment` and `destination-case` already show the
pattern: a `models/` seam with a pinned prompt, a catalog/user-scoped cache keyed
by input + model + prompt, and a deterministic keyless fallback. `Destination`
carries `attributes` (from the vision/enrichment path) and `description`.

## Decisions

### A schema-validated writer
`models/profiles.py:HostedProfileWriter` sends the Destination's known facts and
asks for JSON with a fixed shape: `vibe` (attribute -> 0..1), `typical_stay_days`,
`family_suitability`, `walkability`, `base_camp` (low/medium/high), and `summary`.
`_parse` validates types and ranges and drops unknown fields; anything invalid
yields `{}`.

### Keyless baseline + merge + cache
`catalog/profiles.py:build_profile(conn, destination, facts, writer=None)` starts
from a keyless profile (vibe scores from the Destination's attributes via
`canonicalize`, each at a fixed weight), and, when a writer and facts are present,
merges validated model fields and marks them estimated. The merged profile is
stored in a catalog-scoped `destination_profiles(destination_id, input_hash,
model, prompt_version, payload, source, fetched_at)`, keyed by input hash + model
+ prompt; the keyless baseline is stored when the model fails. `load_profile`
reads the latest.

### Opt-in, never fatal, surfaced
`run_recommend(..., profiles=False, profile_writer=None)` builds profiles for the
recommendations best-effort when enabled; `config.build_profiles` and
`recommend --profiles` expose it. The destination page renders vibe chips and the
suitability fields, marking estimated ones.

## Risks / Trade-offs

- **Model-estimated fields can be wrong** → labelled "estimated", kept separate
  from deterministic fields, validated, and never fatal.
- **Cost** → one call per Destination, cached; the keyless baseline needs none.
- **Vocabulary drift** → vibe keys are restricted to the shared vocabulary.
