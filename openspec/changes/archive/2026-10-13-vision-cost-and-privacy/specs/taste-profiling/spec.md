# Spec Delta

## ADDED Requirements

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
