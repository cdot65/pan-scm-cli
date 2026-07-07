---
"pan-scm-cli": minor
---

Major performance improvements. CLI startup (`scm --help`, `scm --version`) dropped from ~0.42s to ~0.11s via lazy command loading — modules import only when their command is dispatched. OAuth tokens are now cached per context in `~/.scm-cli/cache/` (0600 permissions), eliminating the token + signing-key roundtrips on every invocation; the cache auto-invalidates on rejection or credential change (disable with `SCM_NO_TOKEN_CACHE=1`). Bulk `scm load` commands now apply objects concurrently (5 workers, tune with `SCM_BULK_WORKERS`); position-sensitive rule types still load sequentially to preserve order.
