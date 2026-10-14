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
Matching SHALL be word-boundary based, and each match SHALL be weighted by how
specific it is to the profile as well as how often it recurs.

#### Scenario: Attribute match outranks a non-match
- **WHEN** the profile favours a coastal taste and two candidates are otherwise
  similar, one described as coastal and one inland
- **THEN** the coastal candidate ranks above the inland one

#### Scenario: No substring false positives
- **WHEN** a destination's text contains a word that merely contains an attribute
  term as a substring (for example "earth" containing "art")
- **THEN** no match is recorded for that attribute

#### Scenario: Specific attributes weigh more
- **WHEN** two attributes match a Destination and one is far more specific to the
  profile than the other
- **THEN** the more specific attribute contributes more to the score

#### Scenario: Combined score is deterministic
- **WHEN** the same profile, catalog, and embeddings are ranked twice
- **THEN** the order is identical

### Requirement: Embedding similarity discriminates destinations
The system SHALL use embedding similarity between the Taste Profile facets and
the Destination representation as a signal that distinguishes otherwise similar
candidates.

#### Scenario: Closer embedding ranks higher
- **WHEN** two candidates share the same canonical attributes and one is closer
  to the taste embedding
- **THEN** the closer candidate ranks above the other

#### Scenario: Facets contribute without one dominating
- **WHEN** several taste facets contribute to a Destination's embedding score
- **THEN** the score reflects the best-matching facet rather than a magnitude-dominated average

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

### Requirement: Ranking consumes feedback

The system SHALL incorporate the user's recorded feedback into ranking, applying
a deterministic bias per Destination and leaving ranking unchanged when no
feedback exists.

#### Scenario: Feedback applied
- **WHEN** a Destination has recorded feedback and rankings are produced
- **THEN** its score reflects the feedback bias

#### Scenario: No feedback, no change
- **WHEN** no feedback exists
- **THEN** the ranking matches the feedback-free ranking

### Requirement: Diversify the ranked list

The system SHALL select the returned Recommendations so they are both high-scoring
and mutually dissimilar, rather than the independently highest-scoring items,
using a tunable diversity weight.

#### Scenario: Near-duplicates avoided

- **WHEN** several top-scoring candidate Destinations are very similar to each other
- **THEN** the list includes dissimilar alternatives instead of only the near-duplicates

#### Scenario: Deterministic

- **WHEN** the same inputs are ranked twice with the same diversity weight
- **THEN** the selected list is identical

### Requirement: Novelty preference biases selection

The system SHALL accept a novelty preference — familiar, balanced, or uncommon —
and bias selection toward well-known or less-known Destinations accordingly.

#### Scenario: Familiar preference

- **WHEN** the preference is familiar and a popular destination and an obscure one are otherwise comparable
- **THEN** the popular destination is preferred

#### Scenario: Uncommon preference

- **WHEN** the preference is uncommon and a popular destination and an obscure one are otherwise comparable
- **THEN** the obscure destination is preferred

#### Scenario: Balanced preference

- **WHEN** the preference is balanced
- **THEN** selection does not favour popularity either way

### Requirement: Optional climate preference
The system SHALL accept an optional climate weight and season preference that
bias ranking toward Destinations whose climate matches the user's preference;
with both unset, ranking MUST be unchanged.

#### Scenario: Climate bias applied
- **WHEN** a positive climate weight is set and Destinations have a climate match
- **THEN** higher-matching Destinations rank above otherwise-equal lower-matching ones

#### Scenario: Season preference
- **WHEN** a season preference is set
- **THEN** Destinations whose best months include that season are preferred

#### Scenario: Off by default
- **WHEN** no climate weight or season is set
- **THEN** the ranking matches the climate-free ranking

### Requirement: Embedding signal is valid for long text
The system SHALL produce a distinguishing embedding for a Destination's text even
when it exceeds the model's context length, so unrelated Destinations do not
collapse to the same vector.

#### Scenario: Long text does not collapse
- **WHEN** two different Destinations have text longer than the model context
- **THEN** their embeddings are not near-identical

#### Scenario: Cache refreshed on change
- **WHEN** the text-embedding behaviour changes
- **THEN** previously cached destination embeddings are recomputed

### Requirement: Image-to-image scoring with text fallback
The system SHALL, when a Destination has a visual vector, score it by the best
taste-facet match against that vector, and otherwise fall back to the text
embedding.

#### Scenario: Image vector preferred
- **WHEN** a Destination has a visual vector
- **THEN** its embedding score uses the visual vector

#### Scenario: Text fallback
- **WHEN** a Destination has no visual vector
- **THEN** its embedding score uses the text vector

### Requirement: Calibrated score components
The system SHALL, when calibration is enabled, rescale the embedding and
attribute components across the candidate pool before blending them, so neither
term dominates by magnitude; with calibration disabled, ranking is unchanged.

#### Scenario: Components calibrated
- **WHEN** calibration is enabled
- **THEN** the embedding and attribute terms are rescaled per pool before the blend

#### Scenario: Off by default
- **WHEN** calibration is not enabled
- **THEN** the ranking matches the uncalibrated ranking

#### Scenario: Deterministic
- **WHEN** the same pool is ranked twice with calibration
- **THEN** the order is identical

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

### Requirement: Brief-constrained candidates
The system SHALL, when the trip brief sets a home location and a maximum travel
distance, exclude candidates beyond that distance, and SHALL use the brief's
season for ranking when no season is given explicitly.

#### Scenario: Travel range applied
- **WHEN** a candidate is farther from home than the brief's maximum
- **THEN** it is excluded from the recommendations

#### Scenario: Season hand-off
- **WHEN** the brief has a season and none is passed explicitly
- **THEN** ranking prefers destinations whose best months include it
