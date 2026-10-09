# Persisted data is user-scoped from day one

Although v1 ships single-user, every persisted record (photos, trips, Taste
Profile entries, Recommendations) carries a `user` identifier, and storage is
SQLite. We chose this over a single-user schema because the app is meant to become
a public multi-user service later, and retrofitting tenancy after the fact is
painful. No authentication is built in v1; the identifier is simply present and
threaded through. SQLite keeps v1 trivial with a clean migration path to Postgres.

Status: accepted
