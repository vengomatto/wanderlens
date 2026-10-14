# Spec Delta

## ADDED Requirements

### Requirement: Recency-weighted facets
The system SHALL be able to weight a trip's taste facet by its recency, using a
configurable half-life, so recent trips count more; with no half-life set, facets
are weighted as before.

#### Scenario: Recency decays old trips
- **WHEN** a half-life is set and a trip is older than a recent one
- **THEN** the older trip contributes less to the facets

#### Scenario: Off by default
- **WHEN** no half-life is set
- **THEN** facets are weighted as before

### Requirement: Optional anti-match penalty
The system SHALL, when a weight is set, apply a capped penalty to a Destination
that matches only catalog-common attributes absent from the profile, and MUST
leave ranking unchanged otherwise.

#### Scenario: Anti-match penalised
- **WHEN** a positive anti-match weight is set and a Destination matches only
  common, uninteresting attributes
- **THEN** its score is reduced

#### Scenario: Off by default
- **WHEN** no anti-match weight is set
- **THEN** ranking is unchanged

### Requirement: Configurable pre-filter
The system SHALL make the candidate pre-filter size configurable so ranking terms
can act over a larger pool than the default.

#### Scenario: Larger pool
- **WHEN** the pre-filter is configured larger
- **THEN** more candidates are eligible before the final selection
