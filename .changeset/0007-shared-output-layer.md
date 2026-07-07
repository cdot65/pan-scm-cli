---
"pan-scm-cli": minor
---

Unified console output across the entire CLI. All show commands now support `--output/-o table|json|yaml` — tables render as rich tables, and json/yaml emit pure machine-readable documents on stdout (pipe-safe with jq etc.). Success (✓), error (✗), warning (⚠), and progress messages are styled consistently and routed to stderr. Every command now uses the shared error handler (consistent `Error <operation>: <message>` + exit 1). Fixed `scm context show` exiting 0 on error and context errors printing to stdout. Secret-bearing fields (passwords, secrets, tokens) are masked in show output.
