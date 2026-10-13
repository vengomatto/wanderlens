# Spec Delta

## ADDED Requirements

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
