---
"pan-scm-cli": patch
---

Build the Docker image from local source instead of installing from PyPI, so the image reflects the current checkout. Consolidate the duplicate `DOCKER.md` files into a single corrected `docker/README.md` with accurate build flags (`--local-only`, `--push`, `--no-cache`), GHCR (not Docker Hub) registry details, and repo-root invocation. Fix the `.dockerignore` so it is actually honored by the build (`docker/Dockerfile.dockerignore`) and includes the package sources.
