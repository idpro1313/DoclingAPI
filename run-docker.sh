#!/bin/bash
# Run docling-external-api standalone service with docker compose
# Usage: ./run-docker.sh [--build] [--detach]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BUILD=false
DETACH=false

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
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--build] [--detach]"
            exit 1
            ;;
    esac
done

echo "=== Docling External API Runner ==="
echo "Project dir: $SCRIPT_DIR"
echo "Build: $BUILD"
echo "Detach: $DETACH"
echo ""

if [ "$BUILD" = true ]; then
    echo "[1/3] Creating uv.lock if needed..."
    if [ ! -f docling-external-api/uv.lock ]; then
        echo "No uv.lock found, generating..."
        cd docling-external-api
        uv lock 2>/dev/null || echo "uv not available, Dockerfile will generate lock"
        cd ..
    fi

    echo "[2/3] Building Docker images..."
    docker compose build --no-cache docling-external-api
else
    echo "[1/3] Skipping build (use --build to rebuild)..."
fi

echo "[2/3] Starting containers..."
if [ "$DETACH" = true ]; then
    docker compose up -d
else
    docker compose up
fi

if [ "$DETACH" = true ]; then
    echo ""
    echo "=== Containers started ==="
    echo "docling-external-api: http://localhost:5002"
    echo "docling-serve:         http://localhost:5001"
    echo ""
    echo "To view logs: docker compose logs -f"
    echo "To stop:      docker compose down"
else
    echo ""
    echo "=== Running (press Ctrl+C to stop) ==="
    docker compose logs -f
fi