#!/bin/bash
# docling-serve Docker Build and Run Script
# Usage: ./run_docker.sh [--build] [--external-model]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

IMAGE_NAME="docling-serve"
IMAGE_TAG="latest"
CONTAINER_NAME="docling-serve"
PORT=5001

EXTERNAL_MODEL_ENABLED="${EXTERNAL_MODEL_ENABLED:-false}"
EXTERNAL_MODEL_URL="${EXTERNAL_MODEL_URL:-http://localhost:11434/v1}"
EXTERNAL_MODEL_TIMEOUT="${EXTERNAL_MODEL_TIMEOUT:-60}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

BUILD=false
RUN_CONTAINER=true
EXTERNAL_MODEL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build) BUILD=true; shift ;;
        --external-model) EXTERNAL_MODEL=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --build          Rebuild the Docker image"
            echo "  --external-model Enable external model API (Ollama/vLLM)"
            exit 0 ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

build_image() {
    log_info "Building Docker image: ${IMAGE_NAME}:${IMAGE_TAG}"
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -t "${IMAGE_NAME}:latest" .
    log_info "Image built successfully!"
}

run_container() {
    log_info "Starting container: ${CONTAINER_NAME}"
    
    if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        log_warn "Image not found locally, building..."
        build_image
    fi
    
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Removing existing container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    fi
    
    DOCKER_CMD="docker run --name ${CONTAINER_NAME} --restart unless-stopped -p ${PORT}:${PORT}"
    
    if [ "$EXTERNAL_MODEL" = true ] || [ "$EXTERNAL_MODEL_ENABLED" = "true" ]; then
        log_info "External model API enabled"
        DOCKER_CMD="${DOCKER_CMD} -e DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true -e DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=${EXTERNAL_MODEL_URL} -e DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=${EXTERNAL_MODEL_TIMEOUT}"
    fi
    
    if [ -n "$DOCLING_SERVE_API_KEY" ]; then
        DOCKER_CMD="${DOCKER_CMD} -e DOCLING_SERVE_API_KEY=${DOCLING_SERVE_API_KEY}"
    fi
    
    DOCKER_CMD="${DOCKER_CMD} -v $(pwd)/data:/data -v $(pwd)/scratch:/tmp/docling-scratch -e DOCLING_SERVE_ENABLE_UI=true -d ${IMAGE_NAME}:${IMAGE_TAG}"
    
    eval ${DOCKER_CMD}
    
    log_info "Container started!"
    log_info "UI available at: http://localhost:${PORT}/ui"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

echo "========================================"
echo "  Docling Serve Docker Script"
echo "========================================"
echo ""

if [ "$BUILD" = true ]; then
    build_image
    echo ""
fi

run_container

log_info "Done! Use 'docker logs -f ${CONTAINER_NAME}' to view logs"