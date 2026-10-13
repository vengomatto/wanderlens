# Spec Delta

## ADDED Requirements

### Requirement: Quality-tiered image preference
The system SHALL prefer the most reputable openly-licensed imagery for a
Destination — Wikimedia Commons *Quality*, *Featured*, and *Valued* images ahead
of generic category images — and SHALL apply a resolution floor, a landscape
preference, and near-duplicate detection so the gallery is high quality.

#### Scenario: Assessed images lead
- **WHEN** a Destination has Quality, Featured, or Valued Commons images
- **THEN** those are placed ahead of generic category images in its gallery

#### Scenario: Resolution and orientation
- **WHEN** a candidate image is below the resolution floor or is an extreme portrait crop
- **THEN** it is deprioritised or excluded in favour of suitable photographs

#### Scenario: Near-duplicates removed
- **WHEN** two candidate images are near-duplicates of one another
- **THEN** only one is kept

### Requirement: Pluggable media sources
The system SHALL obtain images through media-source providers behind a port, so a
new source (for example Openverse, Unsplash, or Pexels) can be added without
changing the pipeline, and a provider that returns nothing or errors MUST NOT
fail the run.

#### Scenario: Provider added
- **WHEN** a configured media source provides images for a Destination
- **THEN** they are used alongside the default sources

#### Scenario: Provider failure
- **WHEN** a media source errors or returns nothing
- **THEN** the remaining sources are tried and the run continues

### Requirement: Openly-licensed images only, with external links
The system SHALL embed only openly-licensed images and MUST NOT embed
proprietary images; it SHALL provide outbound links to external photo searches
for a Destination instead of embedding their files.

#### Scenario: Only open licences embedded
- **WHEN** images are cached for a Destination
- **THEN** each embedded image carries an open licence or public-domain status

#### Scenario: External search linked, not embedded
- **WHEN** a Destination is shown
- **THEN** links to external photo searches are offered without embedding their images
