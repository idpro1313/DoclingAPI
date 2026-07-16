#!/bin/bash
# docling-serve Docker Build and Run Script
# Usage: ./run_docker.sh [--build] [--external-model]

set -e

# Configuration
IMAGE_NAME="docling-serve"
IMAGE_TAG="latest"
CONTAINER_NAME="docling-serve"
PORT=5001

# External model defaults
EXTERNAL_MODEL_ENABLED="${EXTERNAL_MODEL_ENABLED:-false}"
EXTERNAL_MODEL_URL="${EXTERNAL_MODEL_URL:-http://localhost:11434/v1}"
EXTERNAL_MODEL_TIMEOUT="${EXTERNAL_MODEL_TIMEOUT:-60}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Parse arguments
BUILD=false
RUN_CONTAINER=true
EXTERNAL_MODEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD=true
            shift
            ;;
        --external-model)
            EXTERNAL_MODEL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --build          Rebuild the Docker image"
            echo "  --external-model Enable external model API (Ollama/vLLM)"
            echo "  --help           Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  EXTERNAL_MODEL_ENABLED  Enable external models (default: false)"
            echo "  EXTERNAL_MODEL_URL       External API URL (default: http://localhost:11434/v1)"
            echo "  EXTERNAL_MODEL_TIMEOUT  API timeout in seconds (default: 60)"
            echo "  DOCLING_SERVE_API_KEY    API key for authentication"
            echo ""
            echo "Examples:"
            echo "  $0 --build --external-model"
            echo "  EXTERNAL_MODEL_URL=http://ollama:11434/v1 $0 --build"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build the Docker image
build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Build from repo root where docling-serve/ subdirectory exists
    docker build \
        --tag "${IMAGE_NAME}:${IMAGE_TAG}" \
        --tag "${IMAGE_NAME}:latest" \
        --file docling-serve/Dockerfile \
        .
    
    log_info "Image built successfully!"
}

# Run the container
run_container() {
    log_info "Starting container: ${CONTAINER_NAME}"
    
    # Check if image exists, build if not
    if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        log_warn "Image not found locally, building..."
        build_image
    fi
    
    # Stop and remove existing container if it exists
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Removing existing container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    fi
    
    # Build docker run command
    DOCKER_CMD="docker run \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${PORT}:${PORT}"
    
    # Add environment variables for external model
    if [ "$EXTERNAL_MODEL" = true ] || [ "$EXTERNAL_MODEL_ENABLED" = "true" ]; then
        log_info "External model API enabled"
        EXTERNAL_MODEL_ENABLED=true
        DOCKER_CMD="${DOCKER_CMD} \
            -e DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true \
            -e DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=${EXTERNAL_MODEL_URL} \
            -e DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=${EXTERNAL_MODEL_TIMEOUT}"
    fi
    
    # Add API key if set
    if [ -n "$DOCLING_SERVE_API_KEY" ]; then
        DOCKER_CMD="${DOCKER_CMD} \
            -e DOCLING_SERVE_API_KEY=${DOCLING_SERVE_API_KEY}"
    fi
    
    # Add volume mounts for persistent data
    DOCKER_CMD="${DOCKER_CMD} \
        -v $(pwd)/data:/data \
        -v $(pwd)/scratch:/tmp/docling-scratch"
    
    # Add Gradio UI enable flag
    DOCKER_CMD="${DOCKER_CMD} \
        -e DOCLING_SERVE_ENABLE_UI=true"
    
    # Add detached mode and image
    DOCKER_CMD="${DOCKER_CMD} \
        -d \
        ${IMAGE_NAME}:${IMAGE_TAG}"
    
    # Execute the command
    eval ${DOCKER_CMD}
    
    log_info "Container started!"
    log_info "UI available at: http://localhost:${PORT}/ui"
    log_info "API docs at: http://localhost:${PORT}/docs"
    log_info "API scalar at: http://localhost:${PORT}/scalar"
    
    # Show container status
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Main execution
echo "========================================"
echo "  Docling Serve Docker Script"
echo "========================================"
echo ""

if [ "$BUILD" = true ]; then
    build_image
    echo ""
fi

run_container

echo ""
log_info "Done! Container is running."
log_info "Use 'docker logs -f ${CONTAINER_NAME}' to view logs"
log_info "Use 'docker stop ${CONTAINER_NAME}' to stop"