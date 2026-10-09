# Spec Delta

## Purpose

Provides an objective quality signal by holding out a visited Destination and
checking whether the system would re-recommend it from the remaining taste.

## ADDED Requirements

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
