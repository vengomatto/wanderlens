# Design

## Context

See `proposal.md`. `recommendations_view` gives the latest run; the feedback
endpoint (`POST /destinations/{id}/feedback?action=…`) already records and returns
the control fragment. Alpine is vendored.

## Decisions

### Server renders the stack, Alpine advances
`discover_view(conn, user_id)` returns the latest-run recommendations minus any
with an existing feedback action (from `load_feedback`), capped at 25.
`discover.html` renders them all with `x-data="{ i: 0 }"`; `x-show="i === n"`
shows one card. Each action button posts to the feedback endpoint (recording) and
`@click="i++"` advances; `@keydown.window.arrow-right/left` do the same. Because
the card is removed from the set on the next visit (feedback now exists), the
state is consistent without extra tracking.

### No jobs, no spec change
This is read + feedback only; the read-only requirement is untouched.

## Risks / Trade-offs

- **Feedback fails silently** → the action posts best-effort; the card still
  advances, and the action is recorded on reload if it succeeded.
- **Large stacks** → capped at 25.
