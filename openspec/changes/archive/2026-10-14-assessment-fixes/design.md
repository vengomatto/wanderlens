# Design

## Context

See `docs/ASSESSMENT.md` section 3 and `proposal.md`.

## Decisions

- **Home wipe (bug 1):** `profile.html` gives the Pipeline poller
  `hx-target="this"` so it stops inheriting `hx-target="main"` from `<body>`.
  Feedback buttons already target `closest .feedback`; Discover buttons use
  `hx-swap="none"`.
- **DB lock (bug 2):** `db.connect` and the job runner open connections with a
  busy `timeout`; `run_recommend` closes its connection at every exit; and the job
  runner records failures without holding a second write connection.
- **Slash ids (bug 3):** destination routes use the `:path` converter, and a
  `dest_url` helper (percent-quoting with `safe=""`) builds links/srcs; the image
  route takes the id as a path segment with the position as a query parameter.
- **Marker markup (bug 4):** `_clean_title` strips `[[..]]`, an optional alias,
  and `#fragment` from marker `name` values, so titles/ids/QIDs are clean; a test
  uses real marker wikitext.
- **`old_town` (bug 9):** match `old town` before generic `city`, or exclude the
  `old town` sequence from the `city` match.

## Risks / Trade-offs

- **`:path` routes** can be greedy → keep the path param last in each route.
- **Busy timeout** can delay a write rather than fail → acceptable for a
  single-user app.
