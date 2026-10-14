# Spec Delta

## ADDED Requirements

### Requirement: Calibrated score components
The system SHALL, when calibration is enabled, rescale the embedding and
attribute components across the candidate pool before blending them, so neither
term dominates by magnitude; with calibration disabled, ranking is unchanged.

#### Scenario: Components calibrated
- **WHEN** calibration is enabled
- **THEN** the embedding and attribute terms are rescaled per pool before the blend

#### Scenario: Off by default
- **WHEN** calibration is not enabled
- **THEN** the ranking matches the uncalibrated ranking

#### Scenario: Deterministic
- **WHEN** the same pool is ranked twice with calibration
- **THEN** the order is identical
