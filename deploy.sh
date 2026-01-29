#!/bin/bash
IMAGE="ring8688/jasper-server:coverlettertool"
PLATFORM="linux/arm64" # Single-arch support (ARM64)
BUILDER_NAME="multiarch-builder"

echo "Building and pushing image ($PLATFORM): $IMAGE"

# Ensure buildx is available
if ! docker buildx version > /dev/null 2>&1; then
    echo "Error: docker buildx is not available."
    exit 1
fi

# Check if the builder exists, if not create it
if ! docker buildx inspect $BUILDER_NAME > /dev/null 2>&1; then
    echo "Creating new buildx builder: $BUILDER_NAME"
    # Create a new builder instance using the docker-container driver which supports multi-platform builds
    docker buildx create --name $BUILDER_NAME --driver docker-container --bootstrap --use
else
    echo "Using existing builder: $BUILDER_NAME"
    docker buildx use $BUILDER_NAME
fi

# Build and Push
if docker buildx build --platform $PLATFORM -t $IMAGE --push .; then
    echo "✅ Successfully pushed to: $IMAGE"
else
    echo "❌ Build failed."
    exit 1
fi
