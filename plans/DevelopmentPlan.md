# Development Plan: docling-external-api

**PURPOSE:** Создать standalone сервис `docling-external-api` для интеграции внешних OpenAI-compatible API с официальным `docling-serve`. Оригинальный код НЕ изменяется — используется официальный Docker образ.

**VERSION:** 0.3.0
**STATUS:** IMPLEMENTED
**UPDATED:** 2026-07-21

---

## 1. Архитектура

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              Clients                                      │
│                    (POST /v1/convert/source и др.)                       │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP :5002
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│          docling-external-api (port 5002)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server                                                      │  │
│  │  - /v1/convert/source (proxy to docling-serve)                       │  │
│  │  - /health                                                           │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  VLM Handler                                                         │  │
│  │  - Receives image from docling-serve response                        │  │
│  │  - Calls external VLM API (minimax, openai, etc.)                    │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP :5001
                                    ▼
┌───────────────────────────────────────────────────────────────────────────┐
│           docling-serve (OFFICIAL IMAGE - port 5001)                      │
│                    quay.io/docling-project/docling-serve                   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Структура проекта

```
docling-external-api/
├── pyproject.toml                  # FastAPI + dependencies
├── Dockerfile                       # Standalone build
├── docker-compose.yaml              # Two-container setup
├── src/docling_external_api/
│   ├── __init__.py                 # Package exports
│   ├── main.py                     # FastAPI app entry point
│   ├── config.py                   # ExternalApiConfig (Pydantic Settings)
│   ├── models.py                   # Request/Response Pydantic models
│   ├── proxy.py                    # HTTP proxy to docling-serve
│   └── vlm_handler.py              # VLM processing logic
└── tests/
    ├── conftest.py                # pytest fixtures
    ├── test_config.py              # Config tests
    ├── test_models.py              # Models tests
    ├── test_proxy.py               # Proxy tests
    └── test_vlm_handler.py         # VLM handler tests
```

---

## 3. API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/v1/convert/source` | POST | Proxy to docling-serve, add VLM |
| `/ui` | GET | Redirect to docling-serve UI |
| `/docs` | GET | Redirect to docling-serve docs |

---

## 4. Критерии успеха

| ID | Критерий | Статус |
|----|----------|--------|
| AC-1 | Docling-serve не модифицирован | ✅ Official image from quay.io |
| AC-2 | VLM обработка через external-api | ✅ Implemented |
| AC-3 | Конфигурация через env vars | ✅ ExternalApiConfig |
| AC-4 | Масштабируемость | ✅ Каждый сервис независим |
| AC-5 | Fault isolation | ✅ Падение одного не ломает другой |
| AC-6 | Проксирование в docling-serve | ✅ proxy.py |
| AC-7 | Unit tests | ✅ Implemented |

---

## 5. Конфигурация

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCLING_SERVE_URL` | `http://localhost:5001` | URL to docling-serve |
| `EXTERNAL_API_PORT` | `5002` | Port for external-api |
| `EXTERNAL_API_VLM_ENABLED` | `0` | Enable external VLM |
| `EXTERNAL_API_VLM_BASE_URL` | - | VLM API base URL |
| `EXTERNAL_API_VLM_MODEL` | `gpt-4o` | VLM model name |
| `EXTERNAL_API_VLM_API_KEY` | - | VLM API key |

---

## 6. Docker Compose

```bash
docker compose up --build
```

- `docling-serve` — official image (port 5001)
- `docling-external-api` — built from Dockerfile (port 5002)

---

## 7. Быстрый старт

```bash
cd docling-external-api

# Development
uv sync --dev
uv run docling-external-api

# Docker
docker compose up --build

# Проверка
curl http://localhost:5002/health
curl -X POST http://localhost:5002/v1/convert/source \
  -H "Content-Type: application/json" \
  -d '{"sources": [{"kind": "url", "uri": "https://arxiv.org/pdf/2501.17887"}]}'
```

---

## 8. Зависимости

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.4.0",
    "httpx>=0.28.0",
]
```

---

## 9. Завершённые задачи

- [x] Создать `main.py` — FastAPI app
- [x] Создать `proxy.py` — HTTP proxy to docling-serve
- [x] Создать `vlm_handler.py` — VLM processing
- [x] Создать `models.py` — Request/Response models
- [x] Обновить `config.py` — добавить DOCLING_SERVE_URL
- [x] Обновить `Dockerfile` — standalone build
- [x] Обновить `docker-compose.yaml` — два сервиса
- [x] Удалить docling-serve/ (используется official image)
- [x] Написать unit tests
- [x] Обновить test_guide.md

---

## 10. TODO для QA

- [ ] Сборка Docker образа
- [ ] Запуск через docker-compose
- [ ] Проверка health endpoint
- [ ] Проверка проксирования convert endpoint
- [ ] Проверка VLM обогащения (если настроено)

---

**BRANCH:** main
**COMMIT:** 4250756