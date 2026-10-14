# taste-profiling Specification

## Purpose
Builds the Taste Profile from a Photo Archive by grouping Photos into trips,
resolving visited places, and deriving aesthetic and subject signals.

## Requirements

### Requirement: Group photos into trips
The system SHALL group Photos into trips using configurable capture-time gap and
GPS-proximity thresholds, so split boundaries can be tuned per archive.

#### Scenario: Same trip
- **WHEN** photos are captured within a short time window at nearby coordinates
- **THEN** they are grouped into one trip

#### Scenario: Separate trips
- **WHEN** a capture-time gap or a large spatial jump separates photo groups
- **THEN** the groups form separate trips

#### Scenario: Configurable boundaries
- **WHEN** the capture-time gap or spatial-jump thresholds are configured
- **THEN** trips are split according to those configured values

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

### Requirement: Robust taste facets
The system SHALL require a minimum number of Photos for a trip to contribute a
full-weight taste facet; a trip below the threshold contributes a weighted-down
or omitted facet so a one-photo trip does not act as a robust centroid.

#### Scenario: Well-supported trip facet
- **WHEN** a trip has at least the minimum number of Photos
- **THEN** it contributes a full-weight facet

#### Scenario: Thin trip facet
- **WHEN** a trip has fewer Photos than the minimum
- **THEN** its facet is weighted down or omitted rather than treated as a robust centroid

### Requirement: Trips record their location
The system SHALL record a location (centroid) for each trip, derived from its
geotagged photos, so visited areas can be compared spatially.

#### Scenario: Centroid recorded
- **WHEN** a trip contains geotagged photos
- **THEN** the trip stores a latitude and longitude centroid

#### Scenario: No geotagged photos
- **WHEN** a trip has no geotagged photos
- **THEN** it records no centroid and contributes no spatial exclusion

### Requirement: Unreadable photos do not abort profiling
The system SHALL skip a photo it cannot read and count it, so one unreadable file
does not fail the whole profiling run.

#### Scenario: Unreadable photo skipped
- **WHEN** a photo cannot be read or decoded
- **THEN** it is skipped, counted, and the run continues

#### Scenario: Count reported
- **WHEN** profiling finishes
- **THEN** the number of skipped photos is available

### Requirement: Privacy-preserving, low-cost tagging
The system SHALL send the vision model a downscaled, orientation-corrected JPEG
with all EXIF metadata removed, at low detail, so no GPS or timestamp leaves the
machine and the request is small.

#### Scenario: EXIF stripped
- **WHEN** a sampled photo is sent to the vision model
- **THEN** the payload carries no EXIF metadata

#### Scenario: Downscaled
- **WHEN** a sampled photo is sent
- **THEN** its long side is at most the configured cap

### Requirement: Cache tag results
The system SHALL cache a trip's tag result by its sampled photos, model, and
prompt version, so a re-run does not re-send known photos.

#### Scenario: Cache avoids resend
- **WHEN** a trip's sample was already tagged for the same model and prompt
- **THEN** no vision request is made for it

#### Scenario: Retag overrides
- **WHEN** retagging is requested
- **THEN** the cache is bypassed and the photos are re-sent

### Requirement: Tag new trips automatically
The system SHALL tag every trip that lacks subjects, not only when the whole
profile is empty, so new trips gain attributes on the next run.

#### Scenario: New trip tagged
- **WHEN** a trip has no attributes and tagging is enabled
- **THEN** it is tagged on the next run

### Requirement: Dry-run estimate
The system SHALL support an estimate that prints the number of images that would
be sent and an estimated cost, without sending anything.

#### Scenario: Estimate only
- **WHEN** a tagging run is asked to estimate
- **THEN** it prints the image count and estimated cost and sends nothing
