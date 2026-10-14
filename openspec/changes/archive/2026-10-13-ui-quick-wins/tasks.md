# Tasks

- [x] 1.1 Make feedback a POST returning the refresh fragment (HTMX) with a redirect fallback; verify tests for the fragment, the recorded action, and the no-HTMX redirect.
- [x] 1.2 Add `_feedback.html` and wire it into the destination page; verify a render shows the control.
- [x] 1.3 Add feedback/badge styles and mobile fixes (no overflow, wrapping nav, single-column grid), a favicon, and `hx-boost`; verify `TestClient` renders and `test_web` passes.
- [x] 1.4 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
