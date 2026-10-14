# Spec Delta

## ADDED Requirements

### Requirement: Versioned recommendation runs
The system SHALL version each recommendation run and SHALL keep prior runs, with
readers using the latest run so history is preserved.

#### Scenario: Run versioned
- **WHEN** recommendations are generated
- **THEN** a new run id is used and the prior run is retained

#### Scenario: Latest used
- **WHEN** the dashboard reads recommendations
- **THEN** it shows the latest run

### Requirement: Impressions logged
The system SHALL log, per run, which destinations were shown and their order.

#### Scenario: Impressions recorded
- **WHEN** recommendations are generated
- **THEN** the shown destinations and ranks are recorded for that run

### Requirement: Optional feedback bias
The system SHALL, when a weight is set, bias ranking by the user's learned
adjustment vector, and MUST leave ranking unchanged otherwise.

#### Scenario: Bias applied
- **WHEN** a positive bias weight is set
- **THEN** destinations closer to the learned vector rank above otherwise-equal ones

#### Scenario: Off by default
- **WHEN** no bias weight is set
- **THEN** ranking is unchanged
