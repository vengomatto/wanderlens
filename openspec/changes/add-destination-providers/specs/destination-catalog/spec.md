# Spec Delta

## MODIFIED Requirements

### Requirement: Enrich destinations with descriptive text
The system SHALL attach a short natural-language description to each candidate
Destination, drawn from a configurable chain of Description Providers, so ranking
text is meaningful rather than a bare place name.

#### Scenario: Description is attached
- **WHEN** a candidate Destination is enriched
- **THEN** it carries a short descriptive text in addition to its name and country

#### Scenario: No description available
- **WHEN** no provider returns a description for a candidate
- **THEN** the Destination keeps its name and country and remains usable

### Requirement: Descriptions are cached locally
The system SHALL persist enriched Destinations so descriptions are fetched at most
once and subsequent runs work without network access.

#### Scenario: Cache avoids refetch
- **WHEN** the catalog is loaded from a previously enriched cache
- **THEN** no provider request is made

#### Scenario: Offline reuse
- **WHEN** the host has no network access and an enriched cache exists
- **THEN** recommendations still run using the cached descriptions

## ADDED Requirements

### Requirement: Pluggable description providers
The system SHALL obtain descriptions through interchangeable Description
Providers used in a configured order, so Wikimedia is one option rather than the
only source.

#### Scenario: First provider wins
- **WHEN** an earlier provider in the chain returns a non-empty description
- **THEN** later providers are not called for that Destination

#### Scenario: Fallback on empty or failure
- **WHEN** a provider returns nothing or errors
- **THEN** the next provider in the chain is tried

#### Scenario: New provider without caller changes
- **WHEN** a new Description Provider is registered
- **THEN** enrichment uses it without changes to the enrichment caller
