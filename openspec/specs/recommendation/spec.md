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

#### Scenario: Exclusion is local, not by country
- **WHEN** a candidate Destination is far from every visited trip but in the same
  country as one
- **THEN** it is still eligible to be recommended

#### Scenario: Nearby place excluded
- **WHEN** a candidate Destination lies within the exclusion radius of a visited trip
- **THEN** it is not returned as a Recommendation

### Requirement: Explain each recommendation

The system SHALL provide a human-readable, evidence-based explanation for each
Recommendation, naming the closest visited Trip, the recurring attributes it
shares, and whether it is new for the user.

#### Scenario: Explanation content

- **WHEN** a Recommendation is produced
- **THEN** its explanation refers to the user's archive — a visited trip, shared attributes, or both

#### Scenario: Closest trip named

- **WHEN** the Recommendation's closest taste facet belongs to a Trip
- **THEN** the explanation refers to that Trip

#### Scenario: Recurring attributes named

- **WHEN** the Destination shares canonical attributes that recur across the profile
- **THEN** those attributes are named in the explanation

#### Scenario: Novelty stated

- **WHEN** no visited Trip lies near the Destination
- **THEN** the explanation states it is new for the user

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

### Requirement: Ranking identifies the closest visit

The system SHALL, for each scored Destination, identify the taste facet that
matches most strongly and the Trip it came from.

#### Scenario: Closest facet tracked

- **WHEN** taste facets come from several Trips
- **THEN** the strongest-matching facet and its Trip are recorded for the Destination

#### Scenario: No facets

- **WHEN** there are no taste facets
- **THEN** no closest visit is recorded

### Requirement: Ranking reports matched attributes

The system SHALL report the canonical attributes a Destination shares with the
profile, each with its recurrence weight.

#### Scenario: Attributes matched

- **WHEN** a Destination shares canonical attributes with the profile
- **THEN** each shared attribute is reported with its weight

#### Scenario: No attribute matches

- **WHEN** a Destination shares no attributes with the profile
- **THEN** no attributes are reported for it

### Requirement: Recommendations expose their evidence

The system SHALL expose, for each Recommendation, the evidence behind its
explanation — closest Trip, matched attributes, and nearest visited distance — so
it can be shown without recomputation.

#### Scenario: Evidence stored

- **WHEN** Recommendations are persisted
- **THEN** their closest Trip, matched attributes, and nearest visited distance are stored with them

#### Scenario: Evidence read offline

- **WHEN** the web layer renders a destination
- **THEN** it reads the stored evidence and makes no external request

### Requirement: Optional LLM explanation synthesis

The system SHALL optionally synthesise the explanation from the evidence using an
injectable LLM, with a pinned model and prompt, cached per Destination and
evidence, and MUST NOT fail the run on error.

#### Scenario: Explanation synthesised

- **WHEN** synthesis is enabled and succeeds
- **THEN** the Recommendation's explanation is the synthesised text

#### Scenario: Disabled or failed

- **WHEN** synthesis is disabled, unavailable, or errors
- **THEN** the deterministic evidence-based explanation is used and the run continues

#### Scenario: Reproducible reuse

- **WHEN** the same Destination and evidence were synthesised before
- **THEN** the cached explanation is reused rather than regenerated
