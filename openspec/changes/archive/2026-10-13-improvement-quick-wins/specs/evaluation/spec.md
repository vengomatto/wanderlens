# Spec Delta

## ADDED Requirements

### Requirement: Leave-one-trip-out metrics
The system SHALL evaluate ranking by hiding each trip in turn, rebuilding taste
from the rest, and reporting averaged rank metrics (MRR, Recall@10, Recall@50)
for the first destination near the hidden trip.

#### Scenario: Metrics averaged over trips
- **WHEN** evaluation runs over several trips
- **THEN** MRR, Recall@10, and Recall@50 are reported averaged over the trips

#### Scenario: No trips
- **WHEN** there are no trips to evaluate
- **THEN** the report says so and no metrics are produced

### Requirement: Score diagnostics
The system SHALL expose, for a recommendation run, a diagnostic breakdown of the
score components (their spread across the pool), the share of collapsed
destination embeddings, and the attribute and country mix of the top results.

#### Scenario: Diagnostics reported
- **WHEN** a recommendation run is asked for diagnostics
- **THEN** component spread, collapsed-vector share, and top-result mix are printed

### Requirement: Regression gate
The system SHALL provide an evaluation script that prints the metrics and fails
when MRR drops beyond a configured margin against a stored baseline.

#### Scenario: Regression fails
- **WHEN** the script runs and MRR falls beyond the margin
- **THEN** the script exits non-zero
