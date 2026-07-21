# Dockerfile for docling-external-api plugin
# Extends local docling-serve and installs docling-external-api plugin
#
# Build context: .. (project root)
# Dockerfile location: ./docling-external-api/Dockerfile
#
# Build: docker build -f docling-external-api/Dockerfile -t docling-external-api ..
# Run:   docker run -p 5001:5001 docling-external-api

ARG BASE_IMAGE=python:3.12-slim-bookworm
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.8.19

###################################################################################################
# Builder stage                                                                                   #
###################################################################################################

FROM ${BASE_IMAGE} AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-osd \
        libleptonica-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libatomic1 \
    && rm -rf /var/lib/apt/lists/*

ENV TESSDATA_PREFIX=/usr/share/tesseract/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    pip install uv

ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV OMP_NUM_THREADS=4
ENV PYTHONIOENCODING=utf-8
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY --chown=1001:0 ../docling-serve/pyproject.toml .
COPY --chown=1001:0 ../docling-serve/uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    uv pip install --python /app/.venv/bin/python torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    uv sync --frozen --no-dev --no-install-project --all-extras --no-extra flash-attn

COPY --chown=1001:0 ../docling-serve/docling_serve /app/docling_serve

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /app/.venv/bin/python ".[ui]" && \
    uv pip install --python /app/.venv/bin/python /app/docling_serve

COPY --chown=1001:0 ../docling-external-api/src/docling_external_api /app/docling_external_api

RUN echo 'from setuptools import setup; setup(name="docling-external-api", packages=["docling_external_api"], python_requires=">=3.10")' > /tmp/setup.py && \
    cp /tmp/setup.py /app/docling_external_api/setup.py && \
    uv pip install --python /app/.venv/bin/python /app/docling_external_api --no-deps


###################################################################################################
# Runtime stage                                                                                   #
###################################################################################################

FROM ${BASE_IMAGE} AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        curl \
    && rm -rf /var/lib/apt/lists/*

ENV TESSDATA_PREFIX=/usr/share/tesseract/tessdata/
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libmimalloc.so.2

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DOCLING_SERVE_ARTIFACTS_PATH=/app/.cache/docling/models

RUN groupadd --gid 1000 docling && \
    useradd --uid 1000 --gid docling --shell /bin/bash --create-home docling && \
    mkdir -p /app/.cache && \
    chown -R docling:docling /app

USER docling

ENV EXTERNAL_API_VLM_ENABLED=1
ENV EXTERNAL_API_VLM_BASE_URL=http://192.168.101.15:8111/v1
ENV EXTERNAL_API_VLM_MODEL=minimax-m2.7
ENV DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true
ENV DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false
ENV DOCLING_SERVE_ENABLE_UI=1

EXPOSE 5001

CMD ["docling-serve", "run"]