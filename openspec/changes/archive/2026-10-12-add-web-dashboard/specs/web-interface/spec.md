# Spec Delta

## Purpose

A local, read-only web presentation of the Taste Profile, visited Trips, and
Recommendations, reusing the existing core read paths so the app's value is
visible without the CLI.

## ADDED Requirements

### Requirement: Local dashboard over persisted data

The system SHALL serve a read-only web dashboard bound to localhost for a single
user, presenting data the CLI has already persisted, without recomputing or
mutating stored state.

#### Scenario: Launching the dashboard

- **WHEN** the user launches the dashboard
- **THEN** it serves pages on localhost for the configured user

#### Scenario: Existing data shown

- **WHEN** the dashboard is opened after an ingest and a recommend run
- **THEN** it presents the persisted Taste Profile and Recommendations

#### Scenario: No recomputation on view

- **WHEN** a dashboard page is requested
- **THEN** no photo ingestion, tagging, or ranking run is triggered

### Requirement: View the Taste Profile

The system SHALL present the Taste Profile as trips, visited-geography weights,
subject/activity weights, and aesthetic coverage.

#### Scenario: Profile summary

- **WHEN** the user opens the profile view
- **THEN** trips, visited geography, subject weights, and the embedded-photo count are shown

### Requirement: Explore Recommendations

The system SHALL present ranked Recommendations with the destination, the
explanation, and the separate embedding and attribute score components.

#### Scenario: Recommendation cards

- **WHEN** the user opens the recommendations view
- **THEN** each Recommendation shows its destination, rank, score components, and explanation

### Requirement: Visit evidence from the Photo Archive

The system SHALL present, for a visited Trip, the user's own Photos and the
trip's attributes as the evidence behind the taste.

#### Scenario: Trip detail

- **WHEN** the user opens a trip
- **THEN** its Photos are shown as thumbnails alongside its attributes and location

### Requirement: Map visited and recommended places

The system SHALL plot visited Trips and recommended Destinations on a map using
keyless map tiles.

#### Scenario: Places plotted

- **WHEN** the map view is shown
- **THEN** visited trips and recommended destinations appear as markers

### Requirement: Graceful empty states

The system SHALL show a guiding empty state, rather than an error, when the
profile or the recommendations have not been generated yet.

#### Scenario: No profile yet

- **WHEN** the dashboard is opened before any ingestion
- **THEN** it explains how to generate the profile

#### Scenario: No recommendations yet

- **WHEN** the recommendations have not been generated
- **THEN** it explains how to generate them

### Requirement: Render without the model runtime

The system SHALL render the dashboard from persisted data only, without loading
the embedding or vision model runtime.

#### Scenario: Dashboard without models

- **WHEN** any dashboard page is rendered
- **THEN** no embedding or vision model is loaded

### Requirement: Local-only presentation

The system SHALL serve the dashboard and the user's Photos locally and MUST NOT
transmit Photos or profile data to any external service.

#### Scenario: No external calls

- **WHEN** any dashboard page is rendered
- **THEN** no Photo or profile data is sent to an external service
