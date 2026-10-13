# Spec Delta

## ADDED Requirements

### Requirement: Embedding signal is valid for long text
The system SHALL produce a distinguishing embedding for a Destination's text even
when it exceeds the model's context length, so unrelated Destinations do not
collapse to the same vector.

#### Scenario: Long text does not collapse
- **WHEN** two different Destinations have text longer than the model context
- **THEN** their embeddings are not near-identical

#### Scenario: Cache refreshed on change
- **WHEN** the text-embedding behaviour changes
- **THEN** previously cached destination embeddings are recomputed
