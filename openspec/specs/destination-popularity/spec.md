# destination-popularity Specification

## Purpose

Fetches and caches a Destination's popularity from a free source, so the app can
distinguish famous from uncommon places and offer a novelty preference.

## Requirements

### Requirement: Fetch popularity from a free source

The system SHALL derive a Destination's popularity from a free, keyless source
(Wikimedia pageviews) without scraping.

#### Scenario: Popularity derived

- **WHEN** popularity is requested for a Destination with an article
- **THEN** a popularity score is derived from its pageviews

#### Scenario: No signal

- **WHEN** no pageview data is available for a Destination
- **THEN** no popularity is stored for it

### Requirement: Cache popularity locally

The system SHALL persist a Destination's popularity so it is fetched at most once
and later runs work without network access.

#### Scenario: Cache avoids refetch

- **WHEN** popularity already exists for a Destination
- **THEN** no source request is made for it

### Requirement: Classify famous versus uncommon

The system SHALL classify each Destination with a popularity score as famous,
balanced, or uncommon, so the interface can label it.

#### Scenario: Label assigned

- **WHEN** a Destination has a popularity score
- **THEN** it is classified as famous, balanced, or uncommon

### Requirement: Popularity is fetched outside the request path

The system SHALL fetch popularity during recommendation generation, not while
serving web pages, and MUST NOT fail the run when the source is unavailable.

#### Scenario: Fetched during recommendations

- **WHEN** recommendations are generated
- **THEN** popularity for the recommended Destinations is fetched and cached

#### Scenario: Failure tolerated

- **WHEN** the popularity source errors or is unavailable
- **THEN** recommendations are still produced, without popularity

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
