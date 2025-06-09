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

### Running the Container with Context Support

The SCM CLI uses a context-based authentication system that makes it easy to manage multiple SCM tenants. The recommended approach is to mount your context directory into the container:

```bash
# Start the container with context directory mounted
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  pan-scm-cli:latest

# Your contexts are now available in the container
docker exec pan-scm scm context list

# Switch to a specific context
docker exec pan-scm scm context use production

# Run commands with the active context
docker exec pan-scm scm show object address --folder Texas
```

### Authentication Methods

#### Method 1: Context-based (Recommended)

```bash
# Create contexts on your host machine first
scm context create production \
  --client-id "prod@123456789.iam.panserviceaccount.com" \
  --client-secret "your-secret" \
  --tsg-id "123456789"

# Run container with context volume
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  pan-scm-cli:latest

# Use contexts in the container
docker exec pan-scm scm context use production
docker exec pan-scm scm context test
```

#### Method 2: Environment Variables (CI/CD)

```bash
# For CI/CD pipelines, use environment variables
docker run -d \
  --name pan-scm \
  -e SCM_CLIENT_ID=your-client-id \
  -e SCM_CLIENT_SECRET=your-client-secret \
  -e SCM_TSG_ID=your-tsg-id \
  pan-scm-cli:latest
```

### Working with Data Files

```bash
# Mount both contexts and data files
docker run -d \
  --name pan-scm \
  -v ~/.scm-cli:/home/scmuser/.scm-cli \
  -v $(pwd)/data:/home/scmuser/data:ro \
  pan-scm-cli:latest

# Process YAML files
docker exec pan-scm scm load object address --file /home/scmuser/data/addresses.yml

# Interactive shell access
docker exec -it pan-scm /bin/ash
```

### Multi-tenant Operations

```bash
# Run multiple containers for different environments
docker run -d --name scm-prod -v ~/.scm-cli:/home/scmuser/.scm-cli pan-scm-cli:latest
docker run -d --name scm-dev -v ~/.scm-cli:/home/scmuser/.scm-cli pan-scm-cli:latest

# Each container can use different contexts
docker exec scm-prod scm context use production
docker exec scm-dev scm context use development

# Operations are isolated to each tenant
docker exec scm-prod scm backup object address --folder Production
docker exec scm-dev scm set object address --folder Development --name test --ip-netmask 10.0.0.1/32
```

### Container Management

```bash
# Stop and remove container
docker stop pan-scm
docker rm pan-scm

# View logs
docker logs pan-scm

# Remove all stopped containers
docker container prune
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
