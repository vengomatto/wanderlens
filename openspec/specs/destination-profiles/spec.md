# destination-profiles Specification

## Purpose

Builds and caches a structured, schema-validated profile for each Destination —
vibe scores, an estimated stay, suitability, and a summary — keyless by default
and model-enriched when configured.

## Requirements

### Requirement: Structured destination profile
The system SHALL produce, for a Destination, a structured profile with vibe
scores over the vocabulary, an estimated typical stay, suitability fields, and a
short summary, and SHALL cache it.

#### Scenario: Profile produced
- **WHEN** a profile is built for a Destination
- **THEN** it carries vibe scores and suitability fields and is cached

#### Scenario: Keyless baseline
- **WHEN** no model is configured
- **THEN** a keyless baseline profile is produced from the Destination's attributes

### Requirement: Model-enriched fields are validated and labelled
The system SHALL, when a model is configured, validate the model's output against
the schema, cache it by input, model, and prompt, label those fields as
estimated, and fall back to the keyless baseline otherwise.

#### Scenario: Valid output accepted
- **WHEN** the model returns schema-valid fields
- **THEN** they are stored and marked estimated

#### Scenario: Invalid output rejected
- **WHEN** the model output fails validation
- **THEN** the keyless baseline is stored instead and the run continues

#### Scenario: Reproducible reuse
- **WHEN** a profile was already built for the same input, model, and prompt
- **THEN** the cached profile is reused