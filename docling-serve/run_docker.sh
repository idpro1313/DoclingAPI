#!/bin/bash
# docling-serve Docker Build and Run Script
# Usage: ./run_docker.sh [--build|--optimized] [--verbose] [--clear-cache]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Setup logging
LOG_DIR="/opt/logs"
LOG_FILE="${LOG_DIR}/docling-serve-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "${LOG_DIR}" 2>/dev/null || true

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Logging functions
log_step() { printf "\n${BOLD}${CYAN}===>${NC} %s${NC}\n\n" "$1"; }
log_info() { printf "${GREEN}[INFO]${NC} %s\n" "$1"; }
log_warn() { printf "${YELLOW}[WARN]${NC} %s\n" "$1"; }
log_error() { printf "${RED}[ERROR]${NC} %s\n" "$1"; }
log_success() { printf "${GREEN}[OK]${NC} %s\n" "$1"; }

log_step_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') ===> $1" >> "${LOG_FILE}"; }
log_info_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "${LOG_FILE}"; }
log_error_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "${LOG_FILE}"; }
log_success_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] $1" >> "${LOG_FILE}"; }

IMAGE_NAME="docling-serve"
IMAGE_TAG="latest"
CONTAINER_NAME="docling-serve"
PORT=5001

EXTERNAL_MODEL_ENABLED="${EXTERNAL_MODEL_ENABLED:-true}"
EXTERNAL_MODEL_URL="${EXTERNAL_MODEL_URL:-http://192.168.101.15:8111/v1}"
EXTERNAL_MODEL_DEFAULT_MODEL="${EXTERNAL_MODEL_DEFAULT_MODEL:-minimax-m2.7}"
EXTERNAL_MODEL_TIMEOUT="${EXTERNAL_MODEL_TIMEOUT:-60}"

BUILD=false
BUILD_OPTIMIZED=false
RUN_CONTAINER=true
VERBOSE=false
CLEAR_CACHE=false
NO_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build) BUILD=true; shift ;;
        --optimized) BUILD=true; BUILD_OPTIMIZED=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --clear-cache) CLEAR_CACHE=true; shift ;;
        --no-cache) NO_CACHE=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --build           Rebuild Docker image"
            echo "  --optimized       Build using Dockerfile.optimized (~5GB)"
            echo "  --verbose         Verbose build output"
            echo "  --clear-cache     Clear BuildKit cache before building"
            echo "  --no-cache        Build without using cache"
            echo ""
            echo "Example:"
            echo "  ./run_docker.sh --optimized"
            exit 0 ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

if [ "$CLEAR_CACHE" = true ]; then
    log_step "Clearing BuildKit Cache"
    docker builder prune -f --filter type=exec.cachemount 2>/dev/null || true
    docker builder prune -f 2>/dev/null || true
    log_success "Cache cleared"
    echo ""
fi

show_banner() {
    echo "=============================================="
    echo "       Docling Serve Docker Launcher"
    echo "=============================================="
    echo ""
}

build_image() {
    log_step "Building Docker Image"
    log_step_to_file "Building Docker Image"

    echo "  Repository:   ${IMAGE_NAME}"
    echo "  Tag:          ${IMAGE_TAG}"
    echo "  BuildKit:     Enabled (layer caching)"
    PROGRESS_MODE="$([ "$VERBOSE" = true ] && echo plain || echo tty)"
    echo "  Progress:     $PROGRESS_MODE"
    echo ""

    local start_time=$(date +%s)
    local build_cmd="docker build"

    if [ "$NO_CACHE" = true ]; then
        build_cmd="$build_cmd --no-cache"
    fi

    $build_cmd \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --progress="${PROGRESS_MODE}" \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_NAME}:latest" \
        . 2>&1 | tee -a "${LOG_FILE}"

    local build_status=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    if [ $build_status -eq 0 ]; then
        log_success "Image built in ${duration}s"
    else
        log_error "Build FAILED after ${duration}s"
    fi

    local size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo "  Image size: $size"
}

build_optimized() {
    log_step "Building Optimized Docker Image"
    log_info "Using Dockerfile.optimized with selective COPY"
    log_info "Expected size: ~5GB (vs 20GB standard)"
    echo ""

    local start_time=$(date +%s)
    local build_cmd="docker build"

    if [ "$NO_CACHE" = true ]; then
        build_cmd="$build_cmd --no-cache"
    fi

    $build_cmd \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -f Dockerfile.optimized \
        --progress=plain \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_NAME}:latest" \
        -t "${IMAGE_NAME}:optimized" \
        . 2>&1 | tee -a "${LOG_FILE}"

    local build_status=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    if [ $build_status -eq 0 ]; then
        log_success "Optimized image built in ${duration}s"
    else
        log_error "Build FAILED after ${duration}s"
    fi

    local size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo "  Image size: $size"

    return $build_status
}

run_container() {
    log_step "Starting Container"

    echo "  Container:  ${CONTAINER_NAME}"
    echo "  Port:       ${PORT}"
    echo "  Volumes:    ./data:/data, ./scratch:/tmp/docling-scratch"

    # Create volumes
    mkdir -p data scratch 2>/dev/null || true
    chmod 777 data scratch 2>/dev/null || true

    # Remove existing container
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Removing existing container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    fi

    # Build docker run command
    DOCKER_CMD="docker run --name ${CONTAINER_NAME} --restart unless-stopped -p ${PORT}:${PORT}"

    # External model settings
    if [ "$EXTERNAL_MODEL" = true ] || [ "$EXTERNAL_MODEL_ENABLED" = "true" ]; then
        log_info "External model API enabled"
        echo "  Model URL:  ${EXTERNAL_MODEL_URL}"
        DOCKER_CMD="${DOCKER_CMD} \
-e DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true \
-e DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=${EXTERNAL_MODEL_URL} \
-e DOCLING_SERVE_EXTERNAL_MODEL_DEFAULT_MODEL=${EXTERNAL_MODEL_DEFAULT_MODEL} \
-e DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=${EXTERNAL_MODEL_TIMEOUT}"
    fi

    # UI and volumes
    DOCKER_CMD="${DOCKER_CMD} \
-v $(pwd)/data:/data \
-v $(pwd)/scratch:/tmp/docling-scratch \
-e DOCLING_SERVE_ENABLE_UI=true \
-d ${IMAGE_NAME}:${IMAGE_TAG}"

    # Run container
    eval $DOCKER_CMD 2>&1 | tee -a "${LOG_FILE}"

    echo ""
    log_info "Waiting for container to start..."
    sleep 3

    # Check container status
    local status=$(docker inspect --format='{{.State.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
    echo "  Status: $status"

    if [ "$status" = "running" ]; then
        log_success "Container is running"
    else
        log_error "Container failed to start"
        echo "  Check logs: docker logs ${CONTAINER_NAME}"
    fi

    echo ""
    echo "  Access Points:"
    echo "    API:     http://localhost:${PORT}"
    echo "    Docs:    http://localhost:${PORT}/docs"
    echo "    UI:      http://localhost:${PORT}/ui"
    echo ""
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_help() {
    echo ""
    echo "Useful Commands:"
    echo "  View logs:        docker logs -f ${CONTAINER_NAME}"
    echo "  Enter container: docker exec -it ${CONTAINER_NAME} bash"
    echo "  Check health:    curl http://localhost:${PORT}/health"
    echo "  Stop container:  docker stop ${CONTAINER_NAME}"
    echo "  Remove container: docker rm ${CONTAINER_NAME}"
    echo ""
    echo "Build options:"
    echo "  Standard build:  ./run_docker.sh --build"
    echo "  Optimized build:  ./run_docker.sh --optimized"
    echo "  Clear cache:      ./run_docker.sh --clear-cache"
    echo ""
    echo "BuildKit cache persists across git pull (no rebuild needed after pull)"
    echo ""
}

# Main execution
show_banner

echo "Configuration:"
echo "  Build:       $([ "$BUILD" = true ] && echo yes || echo no)"
echo "  Optimized:   $([ "$BUILD_OPTIMIZED" = true ] && echo yes || echo no)"
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
    log_warn "Image not found locally - build required"
    BUILD=true
fi

if [ "$BUILD" = true ]; then
    if [ "$BUILD_OPTIMIZED" = true ]; then
        build_optimized
    else
        build_image
    fi
    echo ""
fi

run_container

echo ""
log_success "Done!"
echo ""
log_info "Full build log: ${LOG_FILE}"
echo ""
show_help