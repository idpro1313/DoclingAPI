# Docling Serve Dockerfile
# Optimized for fast rebuilds with BuildKit cache

# syntax=docker/dockerfile:1.4
# Enable BuildKit features: cache mounts, parallel builds

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN --mount=type=cache,target=/root/.local \
    pip install uv

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Create virtual environment
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV OMP_NUM_THREADS=4
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv

# First sync: install dependencies only (no project install yet)
# Skip flash-attn as it requires CUDA to build
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --python /app/.venv/bin/python --frozen --no-dev --no-install-project --no-extra flash-attn

# Copy source code
COPY docling_serve/ ./docling_serve/

# Install the package (non-editable) to create valid entry points
# Editable install breaks in multi-stage builds due to symlink relocation
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /app/.venv/bin/python .

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set Tesseract data path for OCR
ENV TESSDATA_PREFIX=/usr/share/tesseract/tessdata/

# Offline mode - use locally cached models only
ENV HF_HUB_OFFLINE=1

# Copy virtual environment from builder (includes docling_serve package and entry points)
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN groupadd --gid 1000 docling && \
    useradd --uid 1000 --gid docling --shell /bin/bash --create-home docling && \
    chown -R docling:docling /app
USER docling

# Environment variables with defaults
ENV DOCLING_SERVE_HOST=0.0.0.0
ENV DOCLING_SERVE_PORT=5001
ENV DOCLING_SERVE_ENABLE_UI=true
ENV DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=false
ENV DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=60

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Default command - use console script entry point (like official Containerfile)
CMD ["docling-serve", "run"]