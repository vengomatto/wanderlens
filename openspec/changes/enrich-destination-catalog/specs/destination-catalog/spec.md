# Spec Delta

## ADDED Requirements

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
