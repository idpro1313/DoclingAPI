# Development Plan: docling-external-api as Standalone Service

**PURPOSE:** Рефакторинг `docling-external-api` из pluggy plugin в standalone FastAPI сервис. Docling-serve работает в официальном Docker образе без модификаций.

**VERSION:** 0.3.0
**UPDATED:** 2026-07-21

---

## 1. Новая архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Clients                                      │
│                    (POST /v1/convert/source и др.)                       │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP :5002
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│          docling-external-api (NEW - port 5002)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server                                                      │  │
│  │  - /v1/convert/source (proxy to docling-serve)                       │  │
│  │  - /health                                                            │  │
│  │  - /vlm/... (direct VLM calls if needed)                             │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  VLM Handler                                                          │  │
│  │  - Receives image from docling-serve response                        │  │
│  │  - Calls external VLM API (minimax, openai, etc.)                    │  │
│  │  - Returns enriched result                                           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP :5001
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│           docling-serve (OFFICIAL IMAGE - port 5001)                       │
│                    quay.io/docling-project/docling-serve                   │
│                                                                            │
│  - Document conversion (without VLM processing)                            │
│  - OCR (local)                                                             │
│  - Layout analysis                                                        │
│  - Table structure                                                        │
│  - Returns partial result to external-api                                 │
└───────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────────┐
                    │    External VLM API (port 8111)   │
                    │         minimax-m2.7 etc.         │
                    └───────────────────────────────────┘
```

---

## 2. Компоненты docling-external-api

### 2.1 Структура файлов

```
docling-external-api/
├── pyproject.toml                  # FastAPI + dependencies
├── src/docling_external_api/
│   ├── __init__.py                # Package init
│   ├── main.py                    # FastAPI app entry point (NEW)
│   ├── config.py                  # ExternalApiConfig ( существующий )
│   ├── proxy.py                   # Proxy requests to docling-serve (NEW)
│   ├── vlm_handler.py             # VLM processing logic (NEW)
│   └── models.py                  # Pydantic models for API (NEW)
├── Dockerfile                      # Standalone build (UPDATED)
└── docker-compose.yaml              # Two-container setup (UPDATED)
```

### 2.2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/convert/source` | POST | Proxy to docling-serve, add VLM |
| `/ui` | GET | Redirect to docling-serve UI |

### 2.3 Data Flow

```
1. Client → POST /v1/convert/source
2. external-api → docling-serve /v1/convert/source (without VLM)
3. docling-serve → returns document result (images, text, etc.)
4. external-api → extracts pages needing VLM
5. external-api → calls external VLM API for each page
6. external-api → merges VLM results into document
7. external-api → returns enriched document to client
```

---

## 3. Критерии успеха

| ID | Критерий | Метрика |
|----|----------|---------|
| AC-1 | Docling-serve не модифицирован | Official image from quay.io |
| AC-2 | VLM обработка через external-api | VLM calls go through our service |
| AC-3 | Конфигурация через env vars | EXTERNAL_API_* variables |
| AC-4 | Масштабируемость | Каждый сервис независим |
| AC-5 | Fault isolation | Падение одного не ломает другой |

---

## 4. Docker Compose Architecture

```yaml
services:
  docling-serve:
    image: quay.io/docling-project/docling-serve:latest
    ports:
      - "5001:5001"
    environment:
      - DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false
    volumes:
      - docling-models:/app/.cache/docling/models

  docling-external-api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "5002:5002"
    environment:
      - DOCLING_SERVE_URL=http://docling-serve:5001
      - EXTERNAL_API_VLM_ENABLED=1
      - EXTERNAL_API_VLM_BASE_URL=http://192.168.101.15:8111/v1
      - EXTERNAL_API_VLM_MODEL=minimax-m2.7
    depends_on:
      - docling-serve

volumes:
  docling-models:
```

---

## 5. TODO для Code фазы

- [ ] Создать `src/docling_external_api/main.py` — FastAPI app
- [ ] Создать `src/docling_external_api/proxy.py` — HTTP proxy to docling-serve
- [ ] Создать `src/docling_external_api/vlm_handler.py` — VLM processing
- [ ] Создать `src/docling_external_api/models.py` — Request/Response models
- [ ] Обновить `Dockerfile` — только external-api зависимости
- [ ] Обновить `docker-compose.yaml` — два сервиса
- [ ] Обновить `config.py` — добавить DOCLING_SERVE_URL
- [ ] Написать tests/

---

## 6. Конфигурация

### Новые env vars

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCLING_SERVE_URL` | URL to docling-serve | `http://localhost:5001` |
| `EXTERNAL_API_PORT` | Port for external-api | `5002` |

### Существующие (остаются)

| Variable | Description |
|----------|-------------|
| `EXTERNAL_API_VLM_ENABLED` | Enable external VLM |
| `EXTERNAL_API_VLM_BASE_URL` | VLM API URL |
| `EXTERNAL_API_VLM_MODEL` | VLM model name |

---

**STATUS:** PLANNING
**BRANCH:** refactor/standalone-service