# Tasks

- [x] 1.1 Scope the Pipeline poller (bug 1) and audit other HTMX elements; verify the home page keeps its content after the poll.
- [x] 1.2 Add busy timeouts and close connections so a failed job no longer locks the database (bug 2); verify a test that a failed job is followed by a successful feedback POST.
- [x] 1.3 Route slash destination ids and encode links (bug 3); verify page, image, and feedback for `wv:A/B`.
- [x] 1.4 Clean marker markup and add a real-wikitext test plus gate logging (bug 4); verify clean names/ids.
- [x] 1.5 Stop `old_town` implying `city` (bug 9); verify a vocabulary test.
- [x] 1.6 Run `.venv/bin/python -m pytest -q` and `bash scripts/smoke.sh`; verify both pass.

## Workflow follow-up

- Archive the change once review is satisfied and the specs are synced.
