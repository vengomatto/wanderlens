# Proposal

## Why

From `docs/ASSESSMENT.md`: the improvement plan largely landed, but the review
found real regressions. Two bugs block normal use (the home page wipes itself; a
failed UI job locks the database), destination ids with `/` 404, and the catalog
rewrite made live data worse (marker templates keep raw `[[..]]` markup, so names,
ids, and lookups break, and pages without coordinates are dropped).

## What Changes

- **Home page no longer wipes itself.** The Pipeline poller targets itself, not
  `<main>`.
- **Failed jobs don't lock the database.** Connections get a busy timeout and the
  job's connections are closed, so a failed job cannot wedge later writes.
- **Slash ids are routable.** Destination routes accept a path segment, and links
  encode ids so `wv:London/Wandsworth` works for the page, its image, and its
  feedback POST.
- **Catalog marker markup stripped.** `marker`/`listing` `name` values are cleaned
  (brackets, pipes, fragments) before becoming titles/ids/QIDs, plus a test with
  real marker wikitext and a quality gate that logs drops.
- **`old_town` no longer implies `city`.** The vocabulary no longer over-matches
  the `town` inside `old_town`.
- No **BREAKING** changes.

## Capabilities

### Modified Capabilities
- `web-interface`: no self-overwrite on view; ids with slashes routable.
- `destination-catalog`: marker values cleaned; a quality gate.
- `recommendation`: `old_town` no longer implies `city`.

## Impact

- `wanderlens/web/templates/profile.html`, `wanderlens/web/app.py`,
  `wanderlens/web/views.py`.
- `wanderlens/web/jobs.py`, `wanderlens/db.py`, `wanderlens/pipeline/recommend.py`.
- `wanderlens/catalog/wikivoyage.py`.
- `wanderlens/core/vocabulary.py`.
- Tests.
