# Proposal

## Why

Ranking currently scores Destinations on embedding similarity alone. On the
Malta archive the scores cluster within 0.01 and the top pick is an inland
Madrid suburb (Puente de Vallecas), beating coastal Marbella by 0.0014 — noise.
Meanwhile the photo-derived subject tags (*coastal city, turquoise water*) are
extracted and stored but never used in scoring. See `docs/ROADMAP.md`.

## What Changes

- Score Destinations using the **shared attribute vocabulary**: canonical
  attributes derived from the Taste Profile's subjects, matched against
  canonical attributes derived from each Destination's text.
- Combine attribute match with embedding similarity in one configurable score.
- Keep ranking deterministic and report the components for inspection.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `recommendation`: ranking now incorporates a taste-attribute match, not only
  embedding similarity.

## Impact

- `wanderlens/core/recommend.py` — attribute derivation and combined scoring.
- `wanderlens/core/vocabulary.py` — reused for canonicalization.
- `wanderlens/pipeline/recommend.py` / `evaluate.py` — pass profile attributes
  into ranking.
