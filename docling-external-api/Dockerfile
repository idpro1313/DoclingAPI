# Dockerfile for docling-external-api plugin
# Extends local docling-serve and installs docling-external-api plugin
#
# Build context: .. (project root)
# Dockerfile location: ./docling-external-api/Dockerfile
#
# Build: docker build -f docling-external-api/Dockerfile -t docling-external-api ..
# Run:   docker run -p 5001:5001 docling-external-api

ARG BASE_IMAGE=quay.io/sclorg/python-312-c9s:c9s
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.8.19
ARG MIMALLOC_VERSION=v3.2.8

###################################################################################################
# Build mimalloc                                                                                  #
###################################################################################################

FROM ${BASE_IMAGE} AS mimalloc

ARG MIMALLOC_VERSION

USER 0

RUN dnf install -y --best --nodocs --setopt=install_weak_deps=False gcc gcc-c++ make cmake git && \
    git clone --depth 1 --branch ${MIMALLOC_VERSION} https://github.com/microsoft/mimalloc.git /opt/app-root/src/mimalloc && \
    cd /opt/app-root/src/mimalloc && \
    mkdir -p out/release && \
    cd out/release && \
    cmake ../.. && make


FROM ${BASE_IMAGE} AS docling-base

###################################################################################################
# OS Layer                                                                                        #
###################################################################################################

USER 0

COPY --from=mimalloc /opt/app-root/src/mimalloc/out/release/libmimalloc.so /usr/local/lib/libmimalloc.so

RUN dnf -y install --best --nodocs --setopt=install_weak_deps=False dnf-plugins-core && \
    dnf config-manager --best --nodocs --setopt=install_weak_deps=False --save && \
    dnf config-manager --enable crb && \
    dnf -y update && \
    dnf install -y $(cat /tmp/os-packages.txt) && \
    dnf -y clean all && \
    rm -rf /var/cache/dnf

ENV TESSDATA_PREFIX=/usr/share/tesseract/tessdata/


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

COPY --from=uv_stage /uv /bin/uv

# Use LOCAL docling-serve from ../docling-serve (relative to project root)
WORKDIR /tmp/docling-serve

COPY --chown=1001:0 ../docling-serve/pyproject.toml .
COPY --chown=1001:0 ../docling-serve/uv.lock .
COPY --chown=1001:0 ../docling-serve/os-packages.txt .

RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    umask 002 && \
    uv sync --frozen --no-dev --all-extras

# Copy docling_serve source
COPY --chown=1001:0 ../docling-serve/docling_serve /opt/app-root/src/docling_serve

# Re-sync to include the source
RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
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

# Copy and install docling-external-api plugin
COPY --chown=1001:0 ../docling-external-api/src/docling_external_api /opt/app-root/src/docling_external_api

# Create a simple setup.py for the plugin
RUN echo 'from setuptools import setup; setup(name="docling-external-api", packages=["docling_external_api"], python_requires=">=3.10")' > /tmp/setup.py && \
    mkdir -p /opt/app-root/src/docling_external_api && \
    cp /tmp/setup.py /opt/app-root/src/docling_external_api/setup.py

# Install plugin using pip
RUN --mount=type=cache,target=/opt/app-root/src/.cache/uv,uid=1001 \
    uv pip install /opt/app-root/src/docling_external_api --no-deps --system


###################################################################################################
# Runtime image                                                                                   #
###################################################################################################

FROM docling-external-api-plugin AS runtime

USER 0

# Copy entrypoint script
COPY --chown=0:0 ../docling-external-api/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

USER 1001

ENV LD_PRELOAD=/usr/local/lib/libmimalloc.so

# Default environment variables for external API plugin
ENV EXTERNAL_API_VLM_ENABLED=1
ENV EXTERNAL_API_VLM_BASE_URL=http://192.168.101.15:8111/v1
ENV EXTERNAL_API_VLM_MODEL=minimax-m2.7
ENV DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true
ENV DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false

EXPOSE 5001

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["docling-serve", "run"]