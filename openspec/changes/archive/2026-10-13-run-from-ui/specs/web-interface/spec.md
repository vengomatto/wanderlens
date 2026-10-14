# Spec Delta

## MODIFIED Requirements

### Requirement: Local dashboard over persisted data

The system SHALL serve a web dashboard bound to localhost for a single user,
presenting data the CLI has already persisted. It MUST NOT recompute when a page
is viewed; pipeline work runs only when the user explicitly starts a job.

#### Scenario: Launching the dashboard

- **WHEN** the user launches the dashboard
- **THEN** it serves pages on localhost for the configured user

#### Scenario: Existing data shown

- **WHEN** the dashboard is opened after an ingest and a recommend run
- **THEN** it presents the persisted Taste Profile and Recommendations

#### Scenario: No recomputation on view

- **WHEN** a dashboard page is requested
- **THEN** no photo ingestion, tagging, or ranking run is triggered

#### Scenario: Explicit job runs

- **WHEN** the user explicitly starts a job
- **THEN** the pipeline work runs in the background and its status is shown

## ADDED Requirements

### Requirement: User-started pipeline jobs
The system SHALL let the user start an ingest or recommend job from the
dashboard, run it in the background, and report its status; a single-flight guard
SHALL prevent overlapping runs, and a per-process token SHALL be required on the
start request.

#### Scenario: Start a job
- **WHEN** the user starts an ingest or recommend job
- **THEN** a job is created and runs in the background

#### Scenario: Status reported
- **WHEN** the job status is requested
- **THEN** its state, progress, and message are reported

#### Scenario: Single flight
- **WHEN** a job is already running and another is started
- **THEN** the second is refused rather than run concurrently

#### Scenario: Token required
- **WHEN** a start request arrives without the correct token
- **THEN** it is rejected
