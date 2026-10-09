# Wanderlens core is photo-source agnostic (ports & adapters)

Wanderlens is built as a standalone core (`core/`) that never imports a specific
photo manager, behind a `Photo Source` port. The first adapters are a local-folder
backend (the v1 reference) and — deferred to the roadmap — Immich. We chose this
over binding directly to Immich because the product's differentiator is its own
image recognition, and the app is intended to become public and open-source, where
requiring a self-hosted Immich would be an adoption wall. The trade-off: one extra
interface boundary now, in exchange for owning the recognition core and staying
portable.

Status: accepted
