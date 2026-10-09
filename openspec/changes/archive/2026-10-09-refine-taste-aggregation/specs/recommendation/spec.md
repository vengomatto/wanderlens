# Spec Delta

## MODIFIED Requirements

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
