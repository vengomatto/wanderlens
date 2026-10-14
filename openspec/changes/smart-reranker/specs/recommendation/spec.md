# Spec Delta

## ADDED Requirements

### Requirement: Optional hosted re-ranking
The system SHALL, when a re-ranker is configured, apply it to the final
recommendations to reorder them and write a grounded reason for each, and MUST
leave the order and deterministic explanations unchanged otherwise.

#### Scenario: Re-ranker applied
- **WHEN** a re-ranker is configured and succeeds
- **THEN** the recommendations are reordered and carry the re-ranker's reasons

#### Scenario: Off by default
- **WHEN** no re-ranker is configured
- **THEN** the order and explanations are unchanged

#### Scenario: Failure falls back
- **WHEN** the re-ranker errors
- **THEN** the deterministic order and explanations are used and the run continues
