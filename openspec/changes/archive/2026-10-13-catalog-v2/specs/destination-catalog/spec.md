# Spec Delta

## ADDED Requirements

### Requirement: Stable destination identity
The system SHALL record a Destination's Wikidata QID when its source page exposes
one, and SHALL use it in place of a name search for later lookups (media, region
geometry, popularity).

#### Scenario: QID recorded
- **WHEN** a Destination's page carries a Wikidata item
- **THEN** the Destination records that QID

#### Scenario: QID used for lookups
- **WHEN** a Destination has a QID
- **THEN** later lookups use it rather than searching by name

#### Scenario: No QID
- **WHEN** no QID is available
- **THEN** the Destination is still usable and lookups fall back to the name

### Requirement: Section-aware parsing
The system SHALL derive a Destination's granularity from the section its link
appears in, read list items and marker/listing/regionlist templates (taking
coordinates and QIDs when present), and drop links to the parent country or to
other countries.

#### Scenario: Granularity from section
- **WHEN** a place appears under a Cities section
- **THEN** it is tagged with the city granularity, even if also mentioned elsewhere

#### Scenario: Templates parsed
- **WHEN** a section uses marker or listing templates
- **THEN** the places and their coordinates/QIDs are read

#### Scenario: Noise dropped
- **WHEN** a section links the parent country or another country
- **THEN** that link is not added as a Destination

### Requirement: Configurable coverage
The system SHALL make the candidate countries configurable so the catalog can
extend beyond the hard-coded set.

#### Scenario: Custom countries
- **WHEN** candidate countries are configured
- **THEN** the catalog is built for those countries

### Requirement: Quality gate
The system SHALL be able to require a Destination to have coordinates and a lead
of at least a configured length, logging what it drops.

#### Scenario: Gate applied
- **WHEN** the quality gate is enabled and a candidate lacks coordinates or a
  long-enough lead
- **THEN** it is dropped from the catalog
