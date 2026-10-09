# destination-catalog Specification

## Purpose
Provides a normalized pool of candidate Destinations drawn from external place
data, so recommendations are grounded and reproducible.

## Requirements

### Requirement: Source candidate destinations
The system SHALL retrieve Destination candidates — name, coordinates, country,
attributes, and a short description — from an external place catalog.

#### Scenario: Querying the catalog
- **WHEN** the system requests candidates for an area
- **THEN** it receives Destination records for that area

### Requirement: Normalize place records
The system SHALL normalize place records from any catalog source into a single
Destination shape.

#### Scenario: Mixed sources
- **WHEN** records are drawn from more than one catalog source
- **THEN** they are represented as the same Destination shape

### Requirement: Offline geo naming
The system SHALL resolve place names and coordinates using offline geo data so
the catalog does not depend on a live external geo API.

#### Scenario: No network access
- **WHEN** the host has no network access
- **THEN** place names still resolve from local geo data

### Requirement: Enrich destinations with descriptive text
The system SHALL attach a short natural-language description to each candidate
Destination, drawn from a Wikimedia source, so ranking text is meaningful rather
than a bare place name.

#### Scenario: Description is attached
- **WHEN** a candidate Destination is enriched
- **THEN** it carries a short descriptive text in addition to its name and country

#### Scenario: No description available
- **WHEN** no Wikimedia description can be found for a candidate
- **THEN** the Destination keeps its name and country and remains usable

### Requirement: Descriptions are cached locally
The system SHALL persist enriched Destinations so descriptions are fetched at most
once and subsequent runs work without network access.

#### Scenario: Cache avoids refetch
- **WHEN** the catalog is loaded from a previously enriched cache
- **THEN** no Wikimedia request is made

#### Scenario: Offline reuse
- **WHEN** the host has no network access and an enriched cache exists
- **THEN** recommendations still run using the cached descriptions
