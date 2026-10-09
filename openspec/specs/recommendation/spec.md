# recommendation Specification

## Purpose
Ranks candidate Destinations against the Taste Profile and returns explained
Recommendations of places the user has not yet visited.

## Requirements

### Requirement: Recommend new destinations only
The system SHALL rank candidate Destinations against the Taste Profile and MUST
exclude places the user has already visited.

#### Scenario: Visited place excluded
- **WHEN** a candidate Destination is already a visited place in the Taste Profile
- **THEN** it is not returned as a Recommendation

#### Scenario: New place surfaced
- **WHEN** a candidate Destination matches the Taste Profile and has not been visited
- **THEN** it is eligible to be returned as a Recommendation

#### Scenario: Best-matching facet scores a destination
- **WHEN** a candidate Destination matches any one of the taste facets strongly
- **THEN** it scores on that best-matching facet rather than on an averaged taste

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
