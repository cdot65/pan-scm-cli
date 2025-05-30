#!/bin/bash

# Docker multi-platform build script for pan-scm-cli

# Set variables
IMAGE_NAME="pan-scm-cli"
IMAGE_TAG="latest"
REGISTRY=""  # Add your registry here if needed, e.g., "docker.io/username/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building multi-platform Docker image for pan-scm-cli${NC}"

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}Docker buildx is not available. Please update Docker.${NC}"
    exit 1
fi

# Create buildx builder instance if it doesn't exist
BUILDER_NAME="multiarch-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    echo -e "${YELLOW}Creating buildx builder instance...${NC}"
    docker buildx create --name "$BUILDER_NAME" --use
    docker buildx inspect --bootstrap
else
    echo -e "${YELLOW}Using existing buildx builder instance...${NC}"
    docker buildx use "$BUILDER_NAME"
fi

# Check if we should push or just build locally
if [ -z "$REGISTRY" ]; then
    echo -e "${YELLOW}No registry specified. Building locally without push...${NC}"
    echo -e "${YELLOW}To push to a registry, set REGISTRY variable in this script${NC}"
    
    # Build without push for local use
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        .
else
    # Build and push to registry
    echo -e "${GREEN}Building for linux/amd64 and linux/arm64 and pushing to ${REGISTRY}...${NC}"
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag "${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}" \
        --push \
        .
fi

# Check build status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Multi-platform build completed successfully!${NC}"
    echo -e "${GREEN}Image: ${REGISTRY}${IMAGE_NAME}:${IMAGE_TAG}${NC}"
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi

# Optional: Build and load for specific platform
if [ "$1" == "--local" ]; then
    echo -e "${YELLOW}Building for local platform only...${NC}"
    docker buildx build \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}-local" \
        --load \
        .
    echo -e "${GREEN}Local image built: ${IMAGE_NAME}:${IMAGE_TAG}-local${NC}"
elif [ "$1" == "--amd64" ]; then
    echo -e "${YELLOW}Building AMD64 image and loading locally...${NC}"
    docker buildx build \
        --platform linux/amd64 \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}-amd64" \
        --load \
        .
    echo -e "${GREEN}AMD64 image built: ${IMAGE_NAME}:${IMAGE_TAG}-amd64${NC}"
fi