#!/bin/bash

# Docker multi-platform build script for pan-scm-cli

# Set variables
IMAGE_NAME="pan-scm-cli"
REGISTRY="ghcr.io/cdot65/"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse command line arguments
BUILD_LOCAL=false
PUSH_TO_REGISTRY=false
NO_CACHE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
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
            echo "Unknown option: $1"
            echo "Usage: $0 [--local] [--push] [--no-cache]"
            exit 1
            ;;
    esac
done

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

# Navigate to project root (parent of docker directory)
cd "$(dirname "$0")/.."

# Step 1: Build ARM64 for local use (always)
echo -e "${YELLOW}Building ARM64 image for local use...${NC}"
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
echo -e "${GREEN}✓ ARM64 image built: ${IMAGE_NAME}:local and ${IMAGE_NAME}:apple${NC}"

# Step 2: Build AMD64 for broader compatibility
echo -e "${YELLOW}Building AMD64 image...${NC}"
docker buildx build \
    --platform linux/amd64 \
    --tag "${REGISTRY}${IMAGE_NAME}:latest" \
    $NO_CACHE \
    .

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ AMD64 build failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AMD64 image built: ${REGISTRY}${IMAGE_NAME}:latest${NC}"

# Step 3: Push to registry if requested
if [ "$PUSH_TO_REGISTRY" = true ]; then
    echo -e "${YELLOW}Pushing images to registry...${NC}"
    
    # Push AMD64 as :latest
    docker buildx build \
        --platform linux/amd64 \
        --tag "${REGISTRY}${IMAGE_NAME}:latest" \
        --push \
        $NO_CACHE \
        .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ AMD64 push failed!${NC}"
        exit 1
    fi
    
    # Push ARM64 as :apple
    docker buildx build \
        --platform linux/arm64 \
        --tag "${REGISTRY}${IMAGE_NAME}:apple" \
        --push \
        $NO_CACHE \
        .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ ARM64 push failed!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Images pushed to registry:${NC}"
    echo -e "${GREEN}  - ${REGISTRY}${IMAGE_NAME}:latest (AMD64)${NC}"
    echo -e "${GREEN}  - ${REGISTRY}${IMAGE_NAME}:apple (ARM64)${NC}"
else
    echo -e "${YELLOW}Images built but not pushed. Use --push to push to registry.${NC}"
fi

echo -e "${GREEN}✓ Build process completed successfully!${NC}"
echo -e "${GREEN}Local images available:${NC}"
echo -e "${GREEN}  - ${IMAGE_NAME}:local (ARM64)${NC}"
echo -e "${GREEN}  - ${IMAGE_NAME}:apple (ARM64)${NC}"