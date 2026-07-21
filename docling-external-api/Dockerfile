# Dockerfile for docling-external-api standalone service
# Runs as separate container from official docling-serve

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv /app/.venv && \
    uv sync --no-dev

COPY src/ ./src/

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/src:${PYTHONPATH}"

ENV DOCLING_SERVE_URL=http://docling-serve:5001
ENV EXTERNAL_API_PORT=5002

EXPOSE 5002

CMD ["docling-external-api"]