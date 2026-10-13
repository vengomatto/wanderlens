# Spec Delta

## ADDED Requirements

### Requirement: Synthetic trips carry tags
The generated synthetic archive SHALL include canonical subject tags per trip, so
attribute matching — not only embeddings — is exercised end-to-end.

#### Scenario: Tags present
- **WHEN** the synthetic archive is generated
- **THEN** each synthetic trip has canonical attributes that feed the taste profile

#### Scenario: Attribute ranking exercised
- **WHEN** recommendations run over the synthetic archive
- **THEN** Destinations matching the tagged taste rank above non-matching ones
