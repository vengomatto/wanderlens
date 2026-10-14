# Spec Delta

## ADDED Requirements

### Requirement: Views do not overwrite the page
The web layer SHALL scope every auto-refreshing fragment to a specific element, so
a poll or partial update never replaces the whole page.

#### Scenario: Poller is scoped
- **WHEN** a page with an auto-refreshing fragment is rendered
- **THEN** the fragment updates only its own container

### Requirement: Destination ids are routable
The web layer SHALL route and encode destination ids that contain slashes, so the
destination page, its images, and its feedback work for such ids.

#### Scenario: Slash id works
- **WHEN** a destination id contains a slash
- **THEN** its page, image, and feedback requests succeed
