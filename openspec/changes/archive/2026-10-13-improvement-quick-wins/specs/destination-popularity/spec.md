# Spec Delta

## ADDED Requirements

### Requirement: Percentile popularity classification
The system SHALL classify a Destination's popularity by its percentile within the
catalog rather than by an absolute pageview scale, so the labels are balanced.

#### Scenario: Balanced labels
- **WHEN** popularity is classified across a catalog
- **THEN** famous, balanced, and uncommon each cover roughly a third, and no
  single label exceeds a majority

#### Scenario: Relative to the pool
- **WHEN** a Destination is high relative to the others
- **THEN** it is labelled famous regardless of its absolute pageviews
