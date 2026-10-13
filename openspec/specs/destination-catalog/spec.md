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

### Requirement: OpenStreetMap feature provider
The system SHALL be able to derive a Destination's descriptive attributes from
OpenStreetMap tags, using a free, keyless OSM service.

#### Scenario: Features resolved
- **WHEN** a place resolves in OpenStreetMap with tags such as coastline, beach,
  harbour, or historic
- **THEN** the Destination gains descriptive feature text naming those attributes

#### Scenario: Place not found
- **WHEN** OpenStreetMap has no match for the place
- **THEN** the provider returns nothing and the chain continues

#### Scenario: No API key or fee
- **WHEN** the OpenStreetMap provider is used
- **THEN** it requires no API key and incurs no per-request search fee

### Requirement: Area-level destination catalog
The system SHALL draw recommendation candidates from a travel catalog at **area
granularity** (regions and coherent destinations such as *Costa del Sol* or
*Cinque Terre*), not administrative municipalities.

#### Scenario: Area-level candidates
- **WHEN** the catalog is built for a country
- **THEN** it contains regions and named areas, not only small towns

#### Scenario: Granularity tagged
- **WHEN** a Destination is built from the travel catalog
- **THEN** it records its granularity (region, city, or other destination)

#### Scenario: Location and prose
- **WHEN** a Destination is built
- **THEN** it carries coordinates and a short descriptive extract where available

#### Scenario: Fallback when unavailable
- **WHEN** the travel catalog yields nothing for a country
- **THEN** the system falls back to the offline gazetteer rather than failing

### Requirement: GeoNames is used for reverse geocoding
The system SHALL use the offline gazetteer (GeoNames) to resolve visited trip
locations, independent of the recommendation catalog source.

#### Scenario: Trip resolution
- **WHEN** photos are profiled
- **THEN** trip country/city comes from the offline gazetteer

### Requirement: Normalize destination names
The system SHALL normalize a Destination's display name — stripping parenthetical
qualifiers and normalizing casing — so the catalog is clean and comparable.

#### Scenario: Qualifier stripped
- **WHEN** a Destination name carries a parenthetical qualifier such as "(city, Spain)"
- **THEN** the stored display name omits the qualifier

#### Scenario: Casing normalized
- **WHEN** a Destination name is inconsistently cased
- **THEN** the stored display name is normalized

### Requirement: Deduplicate the catalog
The system SHALL remove catalog entries that duplicate another by normalized name
and country, keeping one.

#### Scenario: Duplicate removed
- **WHEN** two catalog entries share a normalized name and country
- **THEN** only one remains in the catalog

### Requirement: Coherent granularity
The system SHALL assign each Destination a granularity from a consistent,
bounded set so the catalog does not mix ad-hoc kinds.

#### Scenario: Granularity bounded
- **WHEN** a Destination is normalized
- **THEN** its granularity is one of the defined kinds

### Requirement: Wider candidate pool
The system SHALL default to a broader set of candidate countries than the initial
handful.

#### Scenario: More countries
- **WHEN** the default catalog is built
- **THEN** it spans a wider set of countries than the original list
