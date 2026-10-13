# Spec Delta

## ADDED Requirements

### Requirement: Additional free image sources
The system SHALL support additional free, commercial-use image sources —
Openverse, Unsplash, and Pexels — enabled by default (Openverse) or when their
key is configured, all behind the image-source port and best-effort.

#### Scenario: Openverse by default
- **WHEN** media is fetched with default configuration
- **THEN** Openverse is consulted as an additional image source

#### Scenario: Keyed sources enabled
- **WHEN** an Unsplash or Pexels key is configured
- **THEN** that source is consulted and its images are filtered like the others

#### Scenario: Source failure tolerated
- **WHEN** an additional image source errors, is slow, or returns nothing
- **THEN** the remaining sources are used and the run continues
