# Spec Delta

## ADDED Requirements

### Requirement: Weight destinations by taste attributes
The system SHALL score each candidate Destination using canonical attributes
derived from the Taste Profile's subjects, matched against canonical attributes
derived from the Destination's own text, in addition to embedding similarity.

#### Scenario: Attribute match outranks a non-match
- **WHEN** the profile favours a coastal taste and two candidates are otherwise
  similar, one described as coastal and one inland
- **THEN** the coastal candidate ranks above the inland one

#### Scenario: Combined score is deterministic
- **WHEN** the same profile, catalog, and embeddings are ranked twice
- **THEN** the order is identical

### Requirement: Ranking is inspectable
The system SHALL expose the components of a Recommendation's score so the
embedding and attribute contributions can be told apart.

#### Scenario: Components reported
- **WHEN** a Recommendation is produced
- **THEN** its embedding score and attribute score are both available
