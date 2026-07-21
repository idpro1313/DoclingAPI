#!/bin/bash
# docling-serve Docker Build and Run Script
# Usage: ./run_docker.sh [--build] [--external-model] [--verbose]

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

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log_step() { echo -e "\n${BOLD}${CYAN}===>$NC ${BOLD}$1${NC}"; }
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }

BUILD=false
RUN_CONTAINER=true
EXTERNAL_MODEL=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build) BUILD=true; shift ;;
        --external-model) EXTERNAL_MODEL=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "  --build           Rebuild the Docker image"
            echo "  --external-model  Enable external model API (Ollama/vLLM)"
            echo "  --verbose         Verbose Docker build output"
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

show_banner() {
    echo -e "${BOLD}"
    echo "╔════════════════════════════════════════════╗"
    echo "║       Docling Serve Docker Launcher        ║"
    echo "╚════════════════════════════════════════════╝"
    echo -e "${NC}"
}

build_image() {
    log_step "Building Docker Image"

    echo -e "  ${BLUE}Repository:${NC}   ${IMAGE_NAME}"
    echo -e "  ${BLUE}Tag:${NC}          ${IMAGE_TAG}"
    echo -e "  ${BLUE}BuildKit:${NC}     Enabled (layer caching)"
    echo -e "  ${BLUE}Progress:${NC}     ${VERBOSE:+verbose}${VERBOSE:-tty}"
    echo ""

    local start_time=$(date +%s)

    if [ "$VERBOSE" = true ]; then
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --progress=plain \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            .
    else
        DOCKER_BUILDKIT=1 docker build \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --progress=tty \
            -t "${IMAGE_NAME}:${IMAGE_TAG}" \
            -t "${IMAGE_NAME}:latest" \
            . 2>&1 | while IFS= read -r line; do
                if [[ "$line" =~ ^#[[:space:]]([0-9]+)\/([[:space:]]([0-9]+))? ]]; then
                    # Stage progress
                    echo -ne "\r  ${YELLOW}Building...${NC} $line    "
                elif [[ "$line" =~ ^ => ]] && [[ "$line" =~ (CACHED|STEP|Successfully) ]]; then
                    echo ""
                    echo -e "  ${GREEN}$line${NC}"
                fi
            done
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    log_success "Image built in ${duration}s"

    # Show image size
    local size=$(docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "{{.Size}}")
    echo -e "  ${BLUE}Image size:${NC} $size"
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

    echo -e "  ${BLUE}Container:${NC}  ${CONTAINER_NAME}"
    echo -e "  ${BLUE}Port:${NC}         ${PORT}"
    echo -e "  ${BLUE}Volumes:${NC}      ./data:/data, ./scratch:/tmp/docling-scratch"

    # Check if container already exists and remove it
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Removing existing container..."
        docker stop "${CONTAINER_NAME}" 2>/dev/null || true
        docker rm "${CONTAINER_NAME}" 2>/dev/null || true
    fi

    # Build docker run command
    DOCKER_CMD="docker run \
        --name ${CONTAINER_NAME} \
        --restart unless-stopped \
        -p ${PORT}:${PORT} \
        --memory=8g \
        --cpus=4"

    # External model settings
    if [ "$EXTERNAL_MODEL" = true ] || [ "$EXTERNAL_MODEL_ENABLED" = "true" ]; then
        log_info "External model API enabled"
        echo -e "  ${BLUE}Model URL:${NC} ${EXTERNAL_MODEL_URL}"
        DOCKER_CMD="${DOCKER_CMD}
        -e DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true
        -e DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=${EXTERNAL_MODEL_URL}
        -e DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=${EXTERNAL_MODEL_TIMEOUT}"
    fi

    # API key
    if [ -n "$DOCLING_SERVE_API_KEY" ]; then
        DOCKER_CMD="${DOCKER_CMD} -e DOCLING_SERVE_API_KEY=${DOCLING_SERVE_API_KEY}"
    fi

    # Volumes and UI
    DOCKER_CMD="${DOCKER_CMD}
        -v $(pwd)/data:/data
        -v $(pwd)/scratch:/tmp/docling-scratch
        -e DOCLING_SERVE_ENABLE_UI=true
        -d ${IMAGE_NAME}:${IMAGE_TAG}"

    # Run container (parse multi-line command)
    eval $(echo "$DOCKER_CMD" | tr '\n' ' ')

    echo ""

    # Wait for container to be healthy
    log_info "Waiting for container to start..."
    sleep 3

    # Check container status
    local status=$(docker inspect --format='{{.State.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
    echo -e "  ${BLUE}Status:${NC} $status"

    if [ "$status" = "running" ]; then
        log_success "Container is running"
    else
        log_error "Container failed to start. Check logs with: docker logs ${CONTAINER_NAME}"
    fi

    echo ""
    echo -e "${BOLD}  Access Points:${NC}"
    echo -e "  ${GREEN}API:${NC}     http://localhost:${PORT}"
    echo -e "  ${GREEN}Docs:${NC}    http://localhost:${PORT}/docs"
    echo -e "  ${GREEN}UI:${NC}      http://localhost:${PORT}/ui"
    echo ""
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

show_help() {
    echo -e "${BOLD}Useful Commands:${NC}"
    echo ""
    echo "  ${CYAN}View logs:${NC}        docker logs -f ${CONTAINER_NAME}"
    echo "  ${CYAN}Enter container:${NC}   docker exec -it ${CONTAINER_NAME} bash"
    echo "  ${CYAN}Check health:${NC}      curl http://localhost:${PORT}/health"
    echo "  ${CYAN}Stop container:${NC}    docker stop ${CONTAINER_NAME}"
    echo "  ${CYAN}Remove container:${NC}  docker rm ${CONTAINER_NAME}"
    echo "  ${CYAN}Rebuild:${NC}          $0 --build"
    echo ""
}

# Main execution
show_banner

echo -e "${BLUE}Configuration:${NC}"
echo "  ${BLUE}Build:${NC}     ${BUILD:+yes}${BUILD:-no}"
echo "  ${BLUE}Ext Model:${NC} ${EXTERNAL_MODEL:+yes}${EXTERNAL_MODEL:-no}"
echo "  ${BLUE}Verbose:${NC}   ${VERBOSE:+yes}${VERBOSE:-no}"
echo ""

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
    log_warn "Image not found locally"
    if [ "$BUILD" != true ]; then
        log_info "Run without --build to pull from registry, or use --build to build locally"
    fi
fi

if [ "$BUILD" = true ]; then
    build_image
    echo ""
fi

run_container

echo ""
log_success "Done!"
echo ""
show_help