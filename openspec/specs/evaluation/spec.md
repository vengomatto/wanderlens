# evaluation Specification

## Purpose
Provides an objective quality signal by holding out a visited Destination and
checking whether the system would re-recommend it from the remaining taste.

## Requirements

### Requirement: Hold out a visited destination
The system SHALL be able to exclude one visited place from the Taste Profile and
evaluate whether the system re-recommends it from the remaining signal.

#### Scenario: Holding out a place
- **WHEN** the user runs evaluation with a held-out visited place
- **THEN** that place is removed from the Taste Profile used for the check

### Requirement: Report evaluation outcome
The system SHALL report the outcome of the hold-out check, including whether and
at what rank the held-out place was recommended.

#### Scenario: Reporting rank
- **WHEN** the hold-out check completes
- **THEN** the system reports whether the held-out place was recommended and its rank

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
