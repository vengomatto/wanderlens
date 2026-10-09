# Spec Delta

## ADDED Requirements

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
