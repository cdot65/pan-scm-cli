---
"pan-scm-cli": minor
---

Added a global `--debug` flag that enables DEBUG logging (including SDK OAuth/auth traffic, previously impossible to surface) and full tracebacks on unexpected errors. Logging is now configured once at CLI startup with a quiet WARNING default (precedence: `--debug` > `SCM_LOG_LEVEL` > context/settings `log_level` > WARNING); invalid log levels warn instead of crashing. Identity profile upserts no longer swallow update failures — real API errors now surface instead of a misleading create-path error.
