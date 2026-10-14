# Spec Delta

## Purpose

Stores and applies a small, per-user trip brief — party, pace, travel range, home
location, budget, and season — so recommendations can respect how and with whom
the user travels.

## ADDED Requirements

### Requirement: Store the trip brief
The system SHALL store, per user, a trip brief with party (adults and children),
pace, season, maximum travel distance, home location, and budget, editable and
reusable.

#### Scenario: Brief saved
- **WHEN** the user sets brief fields
- **THEN** they are stored for that user and reused on later runs

#### Scenario: Empty brief
- **WHEN** no brief is set
- **THEN** nothing changes about recommendations

### Requirement: Brief narrows the candidate set
The system SHALL, when a home location and a maximum travel distance are set,
exclude candidates farther than that distance from home.

#### Scenario: Far candidates excluded
- **WHEN** a candidate is beyond the maximum travel distance from home
- **THEN** it is not recommended

#### Scenario: Near candidates kept
- **WHEN** a candidate is within the maximum travel distance
- **THEN** it remains eligible

### Requirement: Brief feeds the season
The system SHALL use the brief's season as the ranking season when no season is
given explicitly.

#### Scenario: Season from brief
- **WHEN** the brief has a season and no season is passed explicitly
- **THEN** ranking uses the brief's season
