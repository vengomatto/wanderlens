# Spec Delta

## ADDED Requirements

### Requirement: Zero-shot local tagging
The system SHALL be able to derive each photo's attributes locally by scoring its
local visual embedding against vocabulary prompts, without a hosted call, so
tagging is free and private and can cover every photo.

#### Scenario: Local tagging
- **WHEN** local zero-shot tagging is used
- **THEN** attributes are derived from the photos without any network call

#### Scenario: Every photo covered
- **WHEN** local tagging runs over a trip
- **THEN** all of its photos are considered, not only a small sample

### Requirement: Hosted tagging is optional
The system SHALL default to local tagging and keep the hosted vision model opt-in
for cases local tagging handles poorly.

#### Scenario: Local by default
- **WHEN** tagging is requested without opting in
- **THEN** the local tagger is used

#### Scenario: Hosted opt-in
- **WHEN** hosted tagging is explicitly requested and a key is configured
- **THEN** the hosted model is used instead
