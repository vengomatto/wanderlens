# Spec Delta

## ADDED Requirements

### Requirement: Refresh cached media
The system SHALL support re-fetching media for an already-cached Destination, so
improved sourcing applies without deleting the cache by hand.

#### Scenario: Refresh re-fetches
- **WHEN** media is fetched with refresh enabled and a cache exists
- **THEN** the Destination's media is rebuilt from the sources

#### Scenario: Default is cached
- **WHEN** media is fetched without refresh and a cache exists
- **THEN** the cached media is kept and no source is called

### Requirement: Perceptual near-duplicate detection
The system SHALL drop images that are perceptually near-identical to one already
kept for a Destination, not only ones sharing a title.

#### Scenario: Near-duplicate dropped
- **WHEN** two candidate images are perceptually near-identical
- **THEN** only one is stored for the Destination
