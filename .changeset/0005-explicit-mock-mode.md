---
"pan-scm-cli": minor
---

Mock mode is now explicit. Commands no longer silently fall back to mock data when credentials are missing or invalid — they exit with code 1 and actionable remediation steps. To run without credentials (testing, demos), set `SCM_MOCK=1` or use the `--mock` flag where available. This prevents pipelines from reporting fake success when authentication is broken.
