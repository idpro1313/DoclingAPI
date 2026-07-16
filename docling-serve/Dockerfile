# Docling Serve Dockerfile
# Multi-stage build for optimized image size

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN groupadd --gid 1000 docling && \
    useradd --uid 1000 --gid docling --shell /bin/bash --create-home docling
USER docling

# Copy application code
COPY --chown=docling:docling docling_serve/ ./docling_serve/

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