# Docker Multi-Platform Build Instructions

This guide provides instructions for building a Docker image for `pan-scm-cli` with support for both AMD64 and ARM64 architectures.

## Prerequisites

- Docker Desktop 19.03+ with buildx support
- Docker Hub account (if pushing to registry)

## Quick Start

### 1. Build and Push Multi-Platform Image

```bash
# Update the REGISTRY variable in docker-build.sh with your Docker Hub username
# Example: REGISTRY="docker.io/yourusername/"

# Run the build script
./docker-build.sh
```

### 2. Build for Local Testing Only

```bash
# This builds only for your current platform and loads it locally
./docker-build.sh --local
```

## Manual Build Commands

### Setup Buildx

```bash
# Create a new builder instance
docker buildx create --name multiarch-builder --use

# Bootstrap the builder
docker buildx inspect --bootstrap
```

### Build Multi-Platform Image

```bash
# Build for both AMD64 and ARM64
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag yourusername/pan-scm-cli:latest \
  --push \
  .
```

### Build for Local Platform Only

```bash
# Build and load locally (no push)
docker buildx build \
  --tag pan-scm-cli:local \
  --load \
  .
```

## Usage

### Running the Container

```bash
# Start the container in detached mode
docker run -d \
  --name pan-scm \
  -e SCM_CLIENT_ID=your-client-id \
  -e SCM_CLIENT_SECRET=your-client-secret \
  -e SCM_TSG_ID=your-tsg-id \
  pan-scm-cli:latest

# Access the container with interactive shell
docker exec -it pan-scm /bin/ash

# Run scm commands inside the container
scm list address
scm create address "test-addr" --type ip-netmask --ip-netmask "10.0.0.1"

# Exit the shell (container keeps running)
exit

# Execute commands from outside
docker exec pan-scm scm list address

# Mount config file
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli/config.yaml:/home/scmuser/.scm-cli/config.yaml:ro \
  pan-scm-cli:latest

# Mount config and data files
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli/config.yaml:/home/scmuser/.scm-cli/config.yaml:ro \
  -v $(pwd)/data:/home/scmuser/data:ro \
  pan-scm-cli:latest

# Process YAML files
docker exec pan-scm scm create address --from-file /home/scmuser/data/addresses.yml

# Stop and remove container
docker stop pan-scm
docker rm pan-scm
```

### Using as Base Image

```dockerfile
FROM pan-scm-cli:latest

# Switch back to root for installations
USER root

# Add your customizations
RUN apk add --no-cache curl

# Switch back to scmuser
USER scmuser
```

## Architecture Details

- **Base Image**: Alpine Linux with Python 3.12
- **Multi-stage Build**: Separates build dependencies from runtime
- **Security**: Runs as non-root user (`scmuser`)
- **Size**: Minimal image size (~50MB)
- **Platforms**: linux/amd64, linux/arm64

## Troubleshooting

### Build Issues on Apple Silicon

If you encounter issues building on Apple Silicon:

1. Ensure Docker Desktop is updated to the latest version
2. Enable "Use Rosetta for x86/amd64 emulation on Apple Silicon" in Docker Desktop settings
3. Reset the buildx builder:
   ```bash
   docker buildx rm multiarch-builder
   docker buildx create --name multiarch-builder --use
   ```

### Push Failures

If pushing fails:

1. Login to Docker Hub:

   ```bash
   docker login
   ```

2. Ensure you have push permissions to the repository

3. Check that the image tag includes your registry namespace
