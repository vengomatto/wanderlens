# Proposal

## Why

The "why this is for you" is a fixed template (`core/recommend.py:explain`): it
lists the three heaviest subject tags and the most-visited country, identically
for every destination. It never says *which* of the user's trips a place echoes,
*how closely*, or *which* attributes actually recur across the archive. The
roadmap already asks for a specific, non-vague "why" grounded in the profile;
this change makes the ranking carry that evidence and turns it into a real
explanation.

## What Changes

- **Ranking identifies the closest visit**: the best-matching taste facet is
  tracked together with the Trip it came from, not just its score.
- **Ranking reports matched attributes**: the canonical attributes a Destination
  shares with the profile are reported with their recurrence weight.
- **Nearest visited distance** is computed, so "new for you" is factual.
- **Evidence-based deterministic explanation** replaces the template, naming the
  closest trip, the shared attributes, and novelty.
- **Recommendations expose their evidence**: closest trip, matched attributes,
  and nearest distance are persisted so the web can show them without recompute.
- **Optional injectable LLM synthesis** turns the evidence into two or three
  sentences, with a pinned model and prompt, cached for reproducibility, and
  never failing the run. The deterministic explanation remains the default.
- **Destination page** shows the evidence (closest trip, shared-attribute chips)
  alongside the explanation.
- No **BREAKING** changes: ranking order is unchanged; only richer evidence and
  explanations are added.

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `recommendation`: the explanation becomes evidence-based; the ranking exposes
  the closest visit and matched attributes; recommendations persist their
  evidence; an optional LLM explanation is added.
- `web-interface`: the destination page presents the match evidence (closest
  trip and shared attributes) in addition to the explanation.

## Impact

- `wanderlens/core/models.py`: a `Facet` (vector + trip identity) and the richer
  `Recommendation` evidence fields.
- `wanderlens/core/recommend.py`: facet-identified best match, matched-attribute
  reporting, nearest-distance, and the evidence-based `explain`.
- `wanderlens/pipeline/recommend.py`: build labelled facets and persist the
  evidence; wire the optional synthesizer.
- `wanderlens/core/ports.py`: an `ExplanationSynthesizer` port (LLM is
  injectable; the default lives under `models/`).
- `wanderlens/db.py`: additive recommendation columns (`matched_attributes`,
  `best_trip_id`, `best_trip_label`, `best_facet_similarity`, `nearest_trip_km`)
  and a cached `recommendation_explanations` table.
- `wanderlens/web/`: view model + template/CSS for the evidence chips and
  closest-trip line.
- New tests for facet identity, matched attributes, deterministic explanation,
  persistence, and the optional cached synthesis; ranking order unchanged.
