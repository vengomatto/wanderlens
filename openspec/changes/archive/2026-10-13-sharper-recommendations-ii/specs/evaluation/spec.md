# Spec Delta

## ADDED Requirements

### Requirement: Synthetic evaluation gallery
The system SHALL provide a reproducible synthetic gallery fixture — trips with
known photos, coordinates, and attributes — so ranking quality can be evaluated
without a large real archive.

#### Scenario: Fixture is reproducible
- **WHEN** the synthetic gallery is generated
- **THEN** it produces the same trips, photos, and attributes on every run

#### Scenario: Known-good expectations
- **WHEN** recommendations run against the synthetic gallery
- **THEN** destinations matching the fixture's taste are expected within the top results

### Requirement: Ranking quality metrics
The system SHALL compute precision@k and mean reciprocal rank (MRR) for a ranking
against known relevant destinations.

#### Scenario: Metrics computed
- **WHEN** a ranking and a set of relevant destinations are provided
- **THEN** precision@k and MRR are reported

#### Scenario: Perfect ranking
- **WHEN** every relevant destination is ranked first
- **THEN** precision@k and MRR report their best possible values

#### Scenario: No relevant destination
- **WHEN** no relevant destination appears in the ranking
- **THEN** precision@k and MRR report their worst values without error
