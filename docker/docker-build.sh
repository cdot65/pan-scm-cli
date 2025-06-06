#!/bin/bash

# Docker multi-platform build script for pan-scm-cli

# Set variables
IMAGE_NAME="pan-scm-cli"
REGISTRY="ghcr.io/cdot65/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Docker images for pan-scm-cli${NC}"

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

# Parse command line arguments
BUILD_LOCAL=false
PUSH_TO_REGISTRY=false
NO_CACHE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --local-only)
            BUILD_LOCAL=true
            shift
            ;;
        --push)
            PUSH_TO_REGISTRY=true
            shift
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--local-only] [--push] [--no-cache]"
            echo "  --local-only  : Only build local ARM64 image"
            echo "  --push        : Push images to GitHub Container Registry"
            echo "  --no-cache    : Force rebuild without cache"
            exit 1
            ;;
    esac
done

# Step 1: Build ARM64 for local use (always)
echo -e "${BLUE}Step 1: Building ARM64 image for local use...${NC}"
docker buildx build \
    --platform linux/arm64 \
    --tag "${IMAGE_NAME}:local" \
    --tag "${IMAGE_NAME}:apple" \
    --load \
    $NO_CACHE \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ ARM64 build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ ARM64 image built and loaded locally${NC}"
echo -e "${GREEN}  - ${IMAGE_NAME}:local (for local use)${NC}"
echo -e "${GREEN}  - ${IMAGE_NAME}:apple (for registry push)${NC}"

# If --local-only flag is set, stop here
if [ "$BUILD_LOCAL" = true ]; then
    echo -e "${GREEN}✓ Local build complete!${NC}"
    exit 0
fi

# Step 2: Build AMD64 for broader compatibility
echo -e "${BLUE}Step 2: Building AMD64 image...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --tag "${REGISTRY}${IMAGE_NAME}:latest" \
    $NO_CACHE \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ AMD64 build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AMD64 image built${NC}"

# Step 3: Push to registry if requested
if [ "$PUSH_TO_REGISTRY" = true ]; then
    echo -e "${BLUE}Step 3: Pushing images to GitHub Container Registry...${NC}"

    # First, make sure we're logged in to ghcr.io
    echo -e "${YELLOW}Note: Make sure you're logged in to ghcr.io:${NC}"
    echo -e "${YELLOW}  docker login ghcr.io -u cdot65${NC}"

    # Tag the local ARM64 image for registry
    docker tag "${IMAGE_NAME}:apple" "${REGISTRY}${IMAGE_NAME}:apple"

    # Push ARM64 image
    echo -e "${BLUE}Pushing ARM64 image as :apple tag...${NC}"
    docker push "${REGISTRY}${IMAGE_NAME}:apple"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to push ARM64 image!${NC}"
        exit 1
    fi

    # Push AMD64 image (already tagged correctly)
    echo -e "${BLUE}Pushing AMD64 image as :latest tag...${NC}"
    docker buildx build \
        --platform linux/amd64 \
        --tag "${REGISTRY}${IMAGE_NAME}:latest" \
        --push \
        $NO_CACHE \
        .
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to push AMD64 image!${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Successfully pushed to GitHub Container Registry!${NC}"
    echo -e "${GREEN}  - ${REGISTRY}${IMAGE_NAME}:latest (AMD64)${NC}"
    echo -e "${GREEN}  - ${REGISTRY}${IMAGE_NAME}:apple (ARM64)${NC}"
else
    echo -e "${YELLOW}Images built but not pushed. To push to registry, run:${NC}"
    echo -e "${YELLOW}  $0 --push${NC}"
fi

echo -e "${GREEN}✓ Build process complete!${NC}"