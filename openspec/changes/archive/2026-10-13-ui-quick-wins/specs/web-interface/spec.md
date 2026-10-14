# Spec Delta

## ADDED Requirements

### Requirement: Feedback is a POST that stays put
The web layer SHALL record feedback through a POST request that returns the
refreshed feedback control in place, rather than a GET that writes state and
reloads the page.

#### Scenario: Posting feedback
- **WHEN** the user activates a feedback button
- **THEN** the action is recorded and only the feedback control is refreshed

#### Scenario: No JavaScript
- **WHEN** the request is not an HTMX request
- **THEN** the action is recorded and the page redirects back to the destination

### Requirement: Mobile layout does not overflow
The web layer SHALL render without horizontal overflow at narrow viewports, with
a wrapping navigation and a single-column destination grid.

#### Scenario: Narrow viewport
- **WHEN** the page is rendered at a phone width
- **THEN** it does not scroll horizontally and the navigation wraps

### Requirement: Favicon and boosted navigation
The web layer SHALL provide a favicon and SHALL navigate in-app links without a
full page reload where supported.

#### Scenario: No favicon 404
- **WHEN** the page is loaded
- **THEN** a favicon is available and no favicon request 404s

#### Scenario: Boosted links
- **WHEN** an in-app link is followed
- **THEN** it is handled without a full page reload
