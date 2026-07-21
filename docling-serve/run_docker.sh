#!/bin/bash
# docling-serve Docker Build and Run Script
# Usage: ./run_docker.sh [--build] [--external-model] [--verbose]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Setup logging to /opt/logs
LOG_DIR="/opt/logs"
LOG_FILE="${LOG_DIR}/docling-serve-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "${LOG_DIR}" 2>/dev/null || true

log_step() { printf "\n%b===>%b %b%s%b\n" "${BOLD}${CYAN}" "${NC}" "${BOLD}" "$1" "${NC}"; }
log_info() { printf "%b[INFO]%b %s\n" "${GREEN}" "${NC}" "$1"; }
log_warn() { printf "%b[WARN]%b %s\n" "${YELLOW}" "${NC}" "$1"; }
log_error() { printf "%b[ERROR]%b %s\n" "${RED}" "${NC}" "$1"; }
log_success() { printf "%b[OK]%b %s\n" "${GREEN}" "${NC}" "$1"; }

# Also log to file
log_step_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') ===> $1" >> "${LOG_FILE}"; }
log_info_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1" >> "${LOG_FILE}"; }
log_error_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >> "${LOG_FILE}"; }
log_success_to_file() { echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] $1" >> "${LOG_FILE}"; }

IMAGE_NAME="docling-serve"
IMAGE_TAG="latest"
CONTAINER_NAME="docling-serve"
PORT=5001
CACHE_VOLUME="docling-serve-buildkit-cache"

EXTERNAL_MODEL_ENABLED="${EXTERNAL_MODEL_ENABLED:-false}"
EXTERNAL_MODEL_URL="${EXTERNAL_MODEL_URL:-http://localhost:11434/v1}"
EXTERNAL_MODEL_TIMEOUT="${EXTERNAL_MODEL_TIMEOUT:-60}"

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_step() { printf "\n%b===>%b %b%s%b\n" "${BOLD}${CYAN}" "${NC}" "${BOLD}" "$1" "${NC}"; }
log_info() { printf "%b[INFO]%b %s\n" "${GREEN}" "${NC}" "$1"; }
log_warn() { printf "%b[WARN]%b %s\n" "${YELLOW}" "${NC}" "$1"; }
log_error() { printf "%b[ERROR]%b %s\n" "${RED}" "${NC}" "$1"; }
log_success() { printf "%b[OK]%b %s\n" "${GREEN}" "${NC}" "$1"; }

BUILD=false
BUILD_OPTIMIZED=false
RUN_CONTAINER=true
EXTERNAL_MODEL=false
VERBOSE=false
CLEAR_CACHE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build) BUILD=true; shift ;;
        --optimized) BUILD=true; BUILD_OPTIMIZED=true; shift ;;
        --external-model) EXTERNAL_MODEL=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --clear-cache) CLEAR_CACHE=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --build           Rebuild the Docker image"
            echo "  --optimized       Build using Dockerfile.optimized (faster, smaller image)"
            echo "  --external-model  Enable external model API (Ollama/vLLM)"
            echo "  --verbose         Verbose Docker build output"
            echo "  --clear-cache     Clear BuildKit cache before building"
            echo ""
            echo "Environment variables:"
            echo "  EXTERNAL_MODEL_ENABLED   Enable external model (true/false)"
            echo "  EXTERNAL_MODEL_URL       External model base URL"
            echo "  DOCLING_SERVE_API_KEY    API key for authentication"
            echo "  DOCLING_SERVE_PORT       Port to expose (default: 5001)"
            exit 0 ;;
        *) log_error "Unknown option: $1"; exit 1 ;;
    esac
done

if [ "$CLEAR_CACHE" = true ]; then
    log_step "Clearing BuildKit Cache"
    docker builder prune -f --filter type=exec.cachemount || true
    docker builder prune -f || true
    log_success "Cache cleared"
    echo ""
fi

show_banner() {
    printf "%b" "${BOLD}"
    echo "╔════════════════════════════════════════════╗"
    echo "║       Docling Serve Docker Launcher        ║"
    echo "╚════════════════════════════════════════════╝"
    printf "%b\n" "${NC}"
}

build_image() {
    log_step "Building Docker Image"
    log_step_to_file "Building Docker Image"

    echo "  ${BLUE}Repository:${NC}   ${IMAGE_NAME}"
    echo "  ${BLUE}Tag:${NC}          ${IMAGE_TAG}"
    echo "  ${BLUE}BuildKit:${NC}     Enabled (layer caching)"
    echo "  ${BLUE}Cache:${NC}        Persistent volume: ${CACHE_VOLUME}"
    PROGRESS_MODE="$([ "$VERBOSE" = true ] && echo verbose || echo tty)"
    echo "  ${BLUE}Progress:${NC}     $PROGRESS_MODE"
    echo ""
    log_info_to_file "Dockerfile:"
    grep -v "^#" Dockerfile | grep -v "^$" >> "${LOG_FILE}" 2>/dev/null || true

    local start_time=$(date +%s)

    if [ "$VERBOSE" = true ]; then
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --mount=type=cache,target=/root/.cache/buildkit,sharing=locked \
            --progress=plain \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            . 2>&1 | tee -a "${LOG_FILE}"
    else
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --mount=type=cache,target=/root/.cache/buildkit,sharing=locked \
            --progress=plain \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            . 2>&1 | tee -a "${LOG_FILE}"
    fi

    local build_status=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    if [ $build_status -eq 0 ]; then
        log_success "Image built in ${duration}s"
        log_info_to_file "Build SUCCESS in ${duration}s"
    else
        log_error "Build FAILED after ${duration}s"
        log_error "Check full log at: ${LOG_FILE}"
        log_info_to_file "Build FAILED with status ${build_status}"
        echo ""
        echo "=== LAST 50 LINES OF LOG ==="
        tail -50 "${LOG_FILE}"
    fi

    # Show image size
    local size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo "  ${BLUE}Image size:${NC} $size"
    log_info_to_file "Image size: $size"
}

pull_image() {
    log_step "Pulling Latest Image"
    log_info "This may take a few minutes on first run..."

    local start_time=$(date +%s)

    DOCKER_BUILDKIT=1 docker pull "${IMAGE_NAME}:${IMAGE_TAG}" || {
        log_warn "Failed to pull, building locally..."
        build_image
        return
    }

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log_success "Image pulled in ${duration}s"
}

run_container() {
    log_step "Starting Container"

    echo "  ${BLUE}Container:${NC}  ${CONTAINER_NAME}"
    echo "  ${BLUE}Port:${NC}         ${PORT}"
    echo "  ${BLUE}Volumes:${NC}      ./data:/data, ./scratch:/tmp/docling-scratch"

    # Create volumes if they don't exist and set permissions for container user
    mkdir -p data scratch 2>/dev/null || true
    chmod 777 data scratch 2>/dev/null || true

    # Check if container already exists and remove it
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Removing existing container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    fi

    # Build docker run command with proper port mapping
    DOCKER_CMD="docker run --name ${CONTAINER_NAME} --restart unless-stopped -p ${PORT}:${PORT} --memory=8g --cpus=4"

    # External model settings
    if [ "$EXTERNAL_MODEL" = true ] || [ "$EXTERNAL_MODEL_ENABLED" = "true" ]; then
        log_info "External model API enabled"
        echo "  ${BLUE}Model URL:${NC} ${EXTERNAL_MODEL_URL}"
        DOCKER_CMD="${DOCKER_CMD} -e DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true -e DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=${EXTERNAL_MODEL_URL} -e DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=${EXTERNAL_MODEL_TIMEOUT}"
    fi

    # API key
    if [ -n "$DOCLING_SERVE_API_KEY" ]; then
        DOCKER_CMD="${DOCKER_CMD} -e DOCLING_SERVE_API_KEY=${DOCLING_SERVE_API_KEY}"
    fi

    # Volumes and UI
    DOCKER_CMD="${DOCKER_CMD} -v $(pwd)/data:/data -v $(pwd)/scratch:/tmp/docling-scratch -e DOCLING_SERVE_ENABLE_UI=true -d ${IMAGE_NAME}:${IMAGE_TAG}"

    # Run container
    eval $DOCKER_CMD 2>&1 | tee -a "${LOG_FILE}"

    echo ""

    # Wait for container to be healthy
    log_info "Waiting for container to start..."
    log_info_to_file "Container started, checking status..."

    sleep 3

    # Check container status
    local status=$(docker inspect --format='{{.State.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
    echo "  ${BLUE}Status:${NC} $status"
    log_info_to_file "Container status: $status"

    if [ "$status" = "running" ]; then
        log_success "Container is running"
        log_info_to_file "Container is running"
    else
        log_error "Container failed to start. Check logs with: docker logs ${CONTAINER_NAME}"
        log_error_to_file "Container failed to start"
        echo ""
        echo "=== CONTAINER LOGS ===" | tee -a "${LOG_FILE}"
        docker logs "${CONTAINER_NAME}" 2>&1 | head -100 | tee -a "${LOG_FILE}"
    fi

    echo ""
    printf "%b  Access Points:%b\n" "${BOLD}" "${NC}"
    echo "  ${GREEN}API:${NC}     http://localhost:${PORT}"
    echo "  ${GREEN}Docs:${NC}    http://localhost:${PORT}/docs"
    echo "  ${GREEN}UI:${NC}      http://localhost:${PORT}/ui"
    echo ""
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

build_optimized() {
    log_step "Building Optimized Docker Image"
    log_info "Using Dockerfile.optimized with selective COPY"
    log_info "Expected size: ~5GB (vs 20GB standard)"
    echo "  ${BLUE}Cache:${NC}        Persistent buildkit cache"

    local start_time=$(date +%s)

    if [ "$VERBOSE" = true ]; then
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --mount=type=cache,target=/root/.cache/buildkit,sharing=locked \
            -f Dockerfile.optimized \
            --progress=plain \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            -t "${IMAGE_NAME}:optimized" \
            . 2>&1 | tee -a "${LOG_FILE}"
    else
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --mount=type=cache,target=/root/.cache/buildkit,sharing=locked \
            -f Dockerfile.optimized \
            --progress=tty \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            -t "${IMAGE_NAME}:optimized" \
            . 2>&1 | tee -a "${LOG_FILE}"
    fi

    local build_status=${PIPESTATUS[0]}
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    if [ $build_status -eq 0 ]; then
        log_success "Optimized image built in ${duration}s"
        log_info_to_file "Optimized build SUCCESS in ${duration}s"
    else
        log_error "Build FAILED after ${duration}s"
        log_info_to_file "Build FAILED with status ${build_status}"
    fi

    local size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo "  ${BLUE}Image size:${NC} $size"
    log_info_to_file "Image size: $size"

    return $build_status
}

show_help() {
    printf "%bUseful Commands:%b\n" "${BOLD}" "${NC}"
    echo ""
    echo "  ${CYAN}View logs:${NC}        docker logs -f ${CONTAINER_NAME}"
    echo "  ${CYAN}Enter container:${NC}   docker exec -it ${CONTAINER_NAME} bash"
    echo "  ${CYAN}Check health:${NC}      curl http://localhost:${PORT}/health"
    echo "  ${CYAN}Stop container:${NC}    docker stop ${CONTAINER_NAME}"
    echo "  ${CYAN}Remove container:${NC}  docker rm ${CONTAINER_NAME}"
    echo "  ${CYAN}Rebuild:${NC}          $0 --build"
    echo "  ${CYAN}Optimized build:${NC}   $0 --optimized"
    echo "  ${CYAN}Clear cache:${NC}       $0 --clear-cache"
    echo ""
    echo "  ${BLUE}Cache info:${NC}       BuildKit cache persists across git pull"
    echo "  ${BLUE}Image size:${NC}       Optimized: ~5GB / Standard: ~20GB"
    echo ""
}

# Main execution
show_banner

echo ""
printf "%bConfiguration:%b\n" "${BLUE}" "${NC}"
printf "  ${BLUE}Build:${NC}     %s\n" "$([ "$BUILD" = true ] && echo yes || echo no)"
printf "  ${BLUE}Ext Model:${NC} %s\n" "$([ "$EXTERNAL_MODEL" = true ] && echo yes || echo no)"
printf "  ${BLUE}Verbose:${NC}   %s\n" "$([ "$VERBOSE" = true ] && echo yes || echo no)"
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
    log_warn "Image not found locally"
    if [ "$BUILD" != true ]; then
        log_info "Run without --build to pull from registry, or use --build to build locally"
    fi
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
log_info_to_file "Script completed"
echo ""
show_help