# Proposal

## Why

From `docs/IMPROVEMENT_PLAN.md` (A4): each destination is only a 300-character
blurb, so matching, filtering, and explaining are coarse. A structured profile —
vibe scores, typical stay, family suitability, walkability, crowd season — makes
them precise, and it is computed once per destination, not per user.

## What Changes

- **Structured destination profile.** A schema-validated set of fields computed
  once per destination: vibe scores over the vocabulary, an estimated typical
  stay, family/walkability/base-camp suitability, and a short summary. A keyless
  baseline (vibe from the destination's attributes) is always available; a hosted
  cheap model fills the rest, cached by input + model + prompt, with a pinned
  prompt and validated output.
- **Estimated fields are labelled.** Fields from the model are marked
  "estimated"; deterministic fields are kept separate.
- **Surfaced.** The destination page shows the vibe chips and the profile facts.
- No **BREAKING** changes; the model step is opt-in and never fatal.

## Capabilities

### New Capabilities
- `destination-profiles`: a cached, schema-validated structured profile per
  destination, keyless by default and model-enriched when configured.

### Modified Capabilities
- `web-interface`: the destination page shows the profile.

## Impact

- New `wanderlens/models/profiles.py` (hosted writer) and
  `wanderlens/catalog/profiles.py` (keyless + merge + cache).
- `wanderlens/db.py`: `destination_profiles` (catalog-scoped).
- `wanderlens/pipeline/recommend.py`, `cli/`, `config.py`: opt-in wiring.
- `wanderlens/web/`: profile section.
- Tests for the keyless profile, the model merge/validation, and the cache.
