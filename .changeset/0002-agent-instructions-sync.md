---
"pan-scm-cli": patch
---

Bring `AGENTS.md` and `CLAUDE.md` back in sync with the CLI. Both files now document the correct `scm <action> <category> <object-type>` command model, the full command-module layout, and the previously undocumented `incidents`, `local`, `operations`, and `posture` (BPA) commands plus `setup device` and `quarantined-device`. Removed the non-existent `make fix` target. The two files are now kept as identical mirrors so every coding agent gets the same guidance.
