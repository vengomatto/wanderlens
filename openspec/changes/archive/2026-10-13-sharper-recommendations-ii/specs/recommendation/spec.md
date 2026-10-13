# Spec Delta

## MODIFIED Requirements

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

## ADDED Requirements

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
