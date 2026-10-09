# Spec Delta

## Purpose

Builds the Taste Profile from a Photo Archive by grouping Photos into trips,
resolving visited places, and deriving aesthetic and subject signals.

## ADDED Requirements

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
