# Test Guide: docling-external-api

**VERSION:** 0.3.0
**UPDATED:** 2026-07-21

---

## Overview

Standalone service tests for `docling-external-api` - a FastAPI service that proxies requests to `docling-serve` and optionally enriches results with external VLM APIs.

---

## Architecture Under Test

```
Client → docling-external-api (port 5002) → docling-serve (port 5001)
                    ↓
              External VLM API
```

---

## Test Files

| File | Purpose | Key Tests |
|------|---------|-----------|
| `test_config.py` | ExternalApiConfig settings | docling_serve_url, api_port, get_config singleton |
| `test_models.py` | Pydantic request/response | SourceItem, ConvertSourceRequest, HealthResponse |
| `test_proxy.py` | HTTP proxy logic | convert_document, health_check with mocks |
| `test_vlm_handler.py` | VLM processing | extract_pages, call_vlm, process_with_vlm |

---

## Running Tests

```bash
cd docling-external-api
uv sync --dev
uv run pytest tests/ -v
```

---

## Test Data

| Test Case | Input | Expected Output |
|-----------|-------|-----------------|
| `test_docling_serve_url_config` | Default config | `http://localhost:5001` |
| `test_convert_source_request` | Sources array | Valid ConvertSourceRequest |
| `test_health_response` | All fields | HealthResponse with status |
| `test_extract_pages_from_pages` | `{"pages": [...]}` | List of pages |
| `test_call_vlm_success` | Mock httpx response | VLM response dict |

---

## Critical Log Markers (LDD)

Tests verify these log markers are present:

- `[IMP:6]` - Configuration loading
- `[IMP:7]` - HTTP requests/responses
- `[IMP:8]` - VLM API calls
- `[IMP:9]` - Error handling

---

## Mock Strategy

- `httpx.AsyncClient` - mocked for all HTTP calls
- `get_config()` - mocked to return test config
- No real network calls in tests

---

## Docker Compose for Manual Testing

```bash
cd docling-external-api
docker compose up --build
curl http://localhost:5002/health
curl -X POST http://localhost:5002/v1/convert/source \
  -H "Content-Type: application/json" \
  -d '{"sources": [{"kind": "url", "uri": "https://example.com/doc.pdf"}]}'
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCLING_SERVE_URL` | `http://localhost:5001` | URL to docling-serve |
| `EXTERNAL_API_PORT` | `5002` | Port for this service |
| `EXTERNAL_API_VLM_ENABLED` | `0` | Enable VLM processing |
| `EXTERNAL_API_VLM_BASE_URL` | - | VLM API URL |
| `EXTERNAL_API_VLM_MODEL` | `gpt-4o` | VLM model name |