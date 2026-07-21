#!/bin/bash
# Build and run docling-external-api with Docker
# Usage: ./run-docker.sh [--build] [--detach] [--port PORT]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
BUILD=false
DETACH=false
PORT=5001
IMAGE_NAME="docling-external-api"
CONTAINER_NAME="docling-serve-external"
VOLUME_NAME="docling-models"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --detach|-d)
            DETACH=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--build] [--detach] [--port PORT]"
            exit 1
            ;;
    esac
done

echo "=== Docling External API Docker Runner ==="
echo "Project dir: $PROJECT_DIR"
echo "Port: $PORT"
echo "Build: $BUILD"
echo "Detach: $DETACH"
echo ""

# Stop and remove existing container
echo "[1/4] Cleaning up existing container..."
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Build image if requested
if [ "$BUILD" = true ]; then
    echo "[2/4] Building Docker image..."
    docker build -t "$IMAGE_NAME" -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR"
else
    echo "[2/4] Skipping build (use --build to rebuild)..."
fi

# Create volume for models
echo "[3/4] Creating volume..."
docker volume create "$VOLUME_NAME" 2>/dev/null || true

# Run container
echo "[4/4] Starting container..."
DOCKER_OPTS="-p ${PORT}:5001 --name $CONTAINER_NAME"
DOCKER_OPTS="$DOCKER_OPTS -v ${VOLUME_NAME}:/opt/app-root/src/.cache/docling/models"
DOCKER_OPTS="$DOCKER_OPTS -e EXTERNAL_API_VLM_ENABLED=1"
DOCKER_OPTS="$DOCKER_OPTS -e EXTERNAL_API_VLM_BASE_URL=http://192.168.101.15:8111/v1"
DOCKER_OPTS="$DOCKER_OPTS -e EXTERNAL_API_VLM_MODEL=minimax-m2.7"
DOCKER_OPTS="$DOCKER_OPTS -e DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true"
DOCKER_OPTS="$DOCKER_OPTS -e DOCLING_SERVE_ENABLE_UI=1"
DOCKER_OPTS="$DOCKER_OPTS -e DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false"
DOCKER_OPTS="$DOCKER_OPTS -e DOCLING_SERVE_LOG_LEVEL=INFO"

if [ "$DETACH" = true ]; then
    DOCKER_OPTS="$DOCKER_OPTS -d"
fi

docker run $DOCKER_OPTS "$IMAGE_NAME"

if [ "$DETACH" = true ]; then
    echo ""
    echo "=== Container started ==="
    echo "API: http://localhost:${PORT}"
    echo "UI:  http://localhost:${PORT}/ui"
    echo "Docs: http://localhost:${PORT}/docs"
    echo ""
    echo "To view logs: docker logs -f $CONTAINER_NAME"
    echo "To stop: docker stop $CONTAINER_NAME"
else
    echo ""
    echo "=== Container running (press Ctrl+C to stop) ==="
    docker logs -f "$CONTAINER_NAME"
fi