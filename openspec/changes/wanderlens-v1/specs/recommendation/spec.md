# Spec Delta

## Purpose

Ranks candidate Destinations against the Taste Profile and returns explained
Recommendations of places the user has not yet visited.

## ADDED Requirements

### Requirement: Recommend new destinations only
The system SHALL rank candidate Destinations against the Taste Profile and MUST
exclude places the user has already visited.

#### Scenario: Visited place excluded
- **WHEN** a candidate Destination is already a visited place in the Taste Profile
- **THEN** it is not returned as a Recommendation

#### Scenario: New place surfaced
- **WHEN** a candidate Destination matches the Taste Profile and has not been visited
- **THEN** it is eligible to be returned as a Recommendation

### Requirement: Explain each recommendation
The system SHALL provide a human-readable explanation for each Recommendation,
grounded in the user's own Photos.

#### Scenario: Explanation content
- **WHEN** a Recommendation is produced
- **THEN** it includes a reason referring to the user's archive

### Requirement: Bounded ranked output
The system SHALL return a ranked list of Recommendations bounded by a requested
count.

#### Scenario: Requesting a count
- **WHEN** the user requests a number of Recommendations
- **THEN** the system returns at most that many, in ranked order

### Requirement: Repeatable ranking
The system SHALL produce the same ranking for the same Taste Profile and catalog
inputs.

#### Scenario: Re-running recommendations
- **WHEN** recommendations are requested twice with unchanged inputs
- **THEN** the ranked order is the same
