# Docker

Build and run `pan-scm-cli` as a container image for both AMD64 and ARM64.

The image is built **from the local source tree** (not from PyPI), so it reflects the current checkout. The build context is the repository root and the Dockerfile lives here in `docker/`.

## Prerequisites

- Docker 19.03+ with `buildx` support
- A GitHub Container Registry (GHCR) login, only if you push: `docker login ghcr.io -u <user>`

## Build with the helper script

Run from the **repository root**:

```bash
# Build an ARM64 image for local use only (tags: pan-scm-cli:local, pan-scm-cli:apple)
./docker/docker-build.sh --local-only

# Build ARM64 (local) + AMD64 (ghcr.io/cdot65/pan-scm-cli:latest), without pushing
./docker/docker-build.sh

# Build and push ARM64 (:apple) and AMD64 (:latest) to GHCR
./docker/docker-build.sh --push

# Force a rebuild without cache (combine with any of the above)
./docker/docker-build.sh --no-cache
```

Flags: `--local-only`, `--push`, `--no-cache`. The registry is hard-coded to `ghcr.io/cdot65/` in `docker-build.sh` — edit that variable to publish elsewhere.

## Build manually

From the repository root (note `-f docker/Dockerfile` and the `.` context):

```bash
# Multi-platform build + push
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag ghcr.io/cdot65/pan-scm-cli:latest \
  --push \
  -f docker/Dockerfile .

# Local single-platform build
docker buildx build \
  --tag pan-scm-cli:local \
  --load \
  -f docker/Dockerfile .
```

## Usage

The CLI uses context-based auth for multiple SCM tenants. Mount your context directory into the container:

```bash
docker run -d --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  pan-scm-cli:local

docker exec pan-scm scm context list
docker exec pan-scm scm context use production
docker exec pan-scm scm show object address --folder Texas
```

### Auth methods

**Context-based (recommended)** — create contexts on the host, then mount them (as above):

```bash
scm context create production \
  --client-id "prod@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret" \
  --tsg-id "123456789"
```

**Environment variables (CI/CD):**

```bash
docker run -d --name pan-scm \
  -e SCM_CLIENT_ID=your-client-id \
  -e SCM_CLIENT_SECRET=your-client-secret \
  -e SCM_TSG_ID=your-tsg-id \
  pan-scm-cli:local
```

### Working with data files

```bash
docker run -d --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  -v "$(pwd)/data:/home/scmuser/data:ro" \
  pan-scm-cli:local

docker exec pan-scm scm load object address --file /home/scmuser/data/addresses.yml
docker exec -it pan-scm /bin/ash   # interactive shell
```

### Container management

```bash
docker stop pan-scm && docker rm pan-scm
docker logs pan-scm
```

## Published images

- `ghcr.io/cdot65/pan-scm-cli:latest` — AMD64
- `ghcr.io/cdot65/pan-scm-cli:apple` — ARM64

## Image details

- Base: `python:3.12-alpine`, multi-stage (build deps kept out of the runtime image)
- Installed from local source via `pip install .` (poetry-core backend)
- Runs as non-root user `scmuser`; default shell `/bin/ash`; `CMD sleep infinity` keeps it running for `docker exec`

## Troubleshooting

**Apple Silicon build issues:** update Docker Desktop, enable Rosetta for x86/amd64 emulation, and reset the builder:

```bash
docker buildx rm multiarch-builder
docker buildx create --name multiarch-builder --use
```

**Push failures:** log in with `docker login ghcr.io -u <user>` and confirm you have write access to the `ghcr.io/cdot65/pan-scm-cli` package.
