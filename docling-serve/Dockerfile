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
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN --mount=type=cache,target=/root/.local \
    pip install uv

# Copy dependency files first (better caching)
COPY pyproject.toml uv.lock ./

# Cache mount for uv/pip packages
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --frozen --no-install-project

# Copy source code (changes often, but won't invalidate package cache)
COPY docling_serve/ ./docling_serve/

# Install package with cached dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv pip install --system --no-deps -e .

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
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
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
ENV DOCLING_SERVE_ENABLE_UI=false
ENV DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=false
ENV DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=""
ENV DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=60

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

# Default command - run the application
CMD ["python", "-m", "docling_serve"]