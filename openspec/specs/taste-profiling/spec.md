# taste-profiling Specification

## Purpose
Builds the Taste Profile from a Photo Archive by grouping Photos into trips,
resolving visited places, and deriving aesthetic and subject signals.

## Requirements

### Requirement: Group photos into trips
The system SHALL group Photos into trips using capture-time gaps and GPS
proximity.

#### Scenario: Same trip
- **WHEN** photos are captured within a short time window at nearby coordinates
- **THEN** they are grouped into one trip

#### Scenario: Separate trips
- **WHEN** a capture-time gap or a large spatial jump separates photo groups
- **THEN** the groups form separate trips

### Requirement: Resolve visited places
The system SHALL resolve each trip to a visited country and city using offline
geo data, deriving the visited-geography Preference Factor.

#### Scenario: Resolving a trip location
- **WHEN** a trip's Photos carry coordinates
- **THEN** the trip is labelled with the corresponding country and city

#### Scenario: Trip without usable coordinates
- **WHEN** a trip has no usable coordinates
- **THEN** it contributes no visited-geography signal

### Requirement: Embed every photo
The system SHALL compute a visual embedding for each Photo locally, deriving the
aesthetic Preference Factor without sending the image off the host.

#### Scenario: Photo embedding
- **WHEN** a Photo is ingested
- **THEN** a visual embedding vector is stored for it

### Requirement: Tag a sample with attributes
The system SHALL derive human-readable attribute tags for a representative sample
of each trip using a vision model, deriving the subjects/activities Preference
Factor.

#### Scenario: Trip attribute tags
- **WHEN** a representative sample of a trip is processed
- **THEN** the trip gains attribute tags describing its subjects and activities

### Requirement: Persist the Taste Profile
The system SHALL persist the Taste Profile — visited geography, aesthetic
embeddings, and attribute tags — scoped to a user, in local storage.

#### Scenario: Reading the profile
- **WHEN** the user requests the profile
- **THEN** the persisted Taste Profile for that user is shown

### Requirement: Local embeddings, sampled external calls
The system SHALL transmit only sampled Photos to the hosted vision model; all
embeddings MUST be computed locally.

#### Scenario: Tagging with privacy
- **WHEN** the system derives attribute tags
- **THEN** only the sampled Photos leave the host, never the full archive

### Requirement: Store subjects per trip
The system SHALL record the attributes derived for each trip, so preference can
be measured across trips rather than accumulated globally.

#### Scenario: Per-trip attributes recorded
- **WHEN** a trip is tagged
- **THEN** its canonical attributes are stored against that trip

### Requirement: Weight attributes by trip recurrence
The system SHALL weight each canonical attribute by the proportion of trips in
which it appears, not by the number of photos or tag occurrences.

#### Scenario: Recurring attribute outweighs a one-off
- **WHEN** an attribute appears in several trips and another appears in one
- **THEN** the recurring attribute has the higher weight

#### Scenario: A large album does not dominate
- **WHEN** one trip has far more photos than another
- **THEN** each trip contributes equally to the attribute weights

### Requirement: Per-trip taste facets
The system SHALL represent taste as a set of per-trip facets (one visual centroid
per trip) rather than a single global mean, so adding trips does not flatten the
profile.

#### Scenario: Facets preserved
- **WHEN** the profile is built from several trips
- **THEN** each trip contributes its own facet to the profile

### Requirement: Trips record their location
The system SHALL record a location (centroid) for each trip, derived from its
geotagged photos, so visited areas can be compared spatially.

#### Scenario: Centroid recorded
- **WHEN** a trip contains geotagged photos
- **THEN** the trip stores a latitude and longitude centroid

#### Scenario: No geotagged photos
- **WHEN** a trip has no geotagged photos
- **THEN** it records no centroid and contributes no spatial exclusion
