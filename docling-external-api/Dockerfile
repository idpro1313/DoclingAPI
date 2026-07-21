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
# Base layer                                                                                      #
###################################################################################################

FROM ${BASE_IMAGE} AS docling-base

USER 0

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-osd \
        libleptonica-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        libatomic1 \
        libmimalloc-dev \
    && rm -rf /var/lib/apt/lists/*

ENV TESSDATA_PREFIX=/usr/share/tesseract/

RUN ln -s /usr/lib/x86_64-linux-gnu/libmimalloc.so.2 /usr/local/lib/libmimalloc.so && \
    mkdir -p /opt/app-root/src/.cache && \
    chmod -R 777 /opt/app-root/src/.cache


FROM ${UV_IMAGE} AS uv_stage


FROM docling-base AS docling-serve-base

###################################################################################################
# Docling layer - Use LOCAL docling-serve                                   #
###################################################################################################

USER 1001

WORKDIR /opt/app-root/src

ENV \
    OMP_NUM_THREADS=4 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    PYTHONIOENCODING=utf-8 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/app-root \
    DOCLING_SERVE_ARTIFACTS_PATH=/opt/app-root/src/.cache/docling/models

WORKDIR /tmp/docling-serve

COPY --chown=1001:0 ../docling-serve/pyproject.toml .
COPY --chown=1001:0 ../docling-serve/uv.lock .

RUN --mount=from=uv_stage,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    umask 002 && \
    uv sync --frozen --no-dev --all-extras

COPY --chown=1001:0 ../docling-serve/docling_serve /opt/app-root/src/docling_serve

RUN --mount=from=uv_stage,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    umask 002 && \
    uv sync --frozen --no-dev --all-extras


###################################################################################################
# Plugin layer                                                                                    #
###################################################################################################

FROM docling-serve-base AS docling-external-api-plugin

USER 1001

WORKDIR /opt/app-root/src

COPY --chown=1001:0 ../docling-external-api/src/docling_external_api /opt/app-root/src/docling_external_api

RUN echo 'from setuptools import setup; setup(name="docling-external-api", packages=["docling_external_api"], python_requires=">=3.10")' > /tmp/setup.py && \
    mkdir -p /opt/app-root/src/docling_external_api && \
    cp /tmp/setup.py /opt/app-root/src/docling_external_api/setup.py

RUN --mount=from=uv_stage,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
    uv pip install /opt/app-root/src/docling_external_api --no-deps --system


###################################################################################################
# Runtime image                                                                                   #
###################################################################################################

FROM docling-external-api-plugin AS runtime

USER 0

COPY --chown=0:0 ../docling-external-api/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER 1001

ENV LD_PRELOAD=/usr/local/lib/libmimalloc.so

ENV EXTERNAL_API_VLM_ENABLED=1
ENV EXTERNAL_API_VLM_BASE_URL=http://192.168.101.15:8111/v1
ENV EXTERNAL_API_VLM_MODEL=minimax-m2.7
ENV DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true
ENV DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false

EXPOSE 5001

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["docling-serve", "run"]