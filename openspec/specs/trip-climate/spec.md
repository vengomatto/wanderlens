# trip-climate Specification

## Purpose

Derives each trip's weather and a user's climate preference from free historical
data, cached and user-scoped, so recommendations can account for the weather
someone likes.

## Requirements

### Requirement: Derive trip weather
The system SHALL derive a trip's weather — mean temperature and precipitation —
from free, keyless historical data using the trip's coordinates and dates.

#### Scenario: Weather derived
- **WHEN** a trip has coordinates and dates
- **THEN** its mean temperature and precipitation are derived and cached

#### Scenario: No location or dates
- **WHEN** a trip lacks coordinates or dates
- **THEN** it contributes no weather signal

### Requirement: Build a climate preference
The system SHALL aggregate the trips' weather into a user climate preference —
a comfortable temperature band, precipitation, and preferred months — scoped to
the user.

#### Scenario: Preference built
- **WHEN** several trips have weather
- **THEN** a climate preference is derived and stored for the user

#### Scenario: Insufficient trips
- **WHEN** no trip has weather
- **THEN** no climate preference is stored and nothing else changes

### Requirement: Weather is cached and never fatal
The system SHALL cache weather per trip and MUST NOT fail the run when the
weather source is unavailable.

#### Scenario: Cache avoids refetch
- **WHEN** weather already exists for a trip
- **THEN** no source request is made for it

#### Scenario: Failure tolerated
- **WHEN** the weather source errors or is unavailable
- **THEN** the run continues without that trip's weather
