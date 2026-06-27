---
"pan-scm-cli": patch
---

Migrate the documentation site from MkDocs Material to Docusaurus. Docs now live in `docs-site/`, build to GitHub Pages via a Node-based GitHub Actions workflow, and the MkDocs configuration, Python doc dependencies, and old `docs/` sources have been removed. Published documentation remains at https://cdot65.github.io/pan-scm-cli/.
