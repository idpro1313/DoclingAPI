# Документация проекта DoclingAPI

> Карта для агентов — **`plans/`** (Grace 2): `DevelopmentPlan.md`, `AppGraph.xml`. Журнал — **`docs/HISTORY.md`**.

## Обзор

DoclingAPI — API-сервис для конвертации документов (PDF, DOCX, HTML, изображения) в структурированные форматы (Markdown, JSON) с использованием ML-пайплайнов Docling.

**Ключевые возможности:**
- Синхронная и асинхронная конвертация документов
- VLM/LLM обработка через OpenAI-compatible API (Ollama, vLLM)
- Gradio UI для интерактивного использования
- OpenTelemetry метрики и трейсинг

## Стек

| Компонент | Технология |
|-----------|------------|
| Python | 3.12+ |
| Web Framework | FastAPI + Uvicorn |
| ML Pipeline | Docling, Docling-Jobkit |
| UI | Gradio |
| Контейнеризация | Docker, BuildKit |
| Orchestration | LOCAL (RQ, Ray опционально) |

## Структура репозитория

| Путь | Назначение |
|------|------------|
| `docling-serve/docling_serve/` | Исходный код API-сервиса |
| `docling-serve/Dockerfile` | Docker образ для production |
| `docling-serve/run_docker.sh` | Скрипт запуска Docker |
| `plans/` | План и граф для агента (Grace 2) |
| `docling-serve/tests/` | Тесты, `test_guide.md` для mode-qa |
| `docs/` | Эта документация, `HISTORY.md` |
| `work/` | Вспомогательные артефакты (не в git) |
| `.kilocode/` | Grace 2: rules, skills |

## Быстрый старт

### Локальная разработка

```bash
cd docling-serve
pip install -e ".[ui]"
docling-serve run --enable-ui
# Откройте http://localhost:5001/ui
```

### Docker

```bash
cd docling-serve
./run_docker.sh --build
# Откройте http://localhost:5001/ui
```

### Environment переменные

| Переменная | Default | Описание |
|------------|---------|----------|
| `DOCLING_SERVE_PORT` | 5001 | Порт сервера |
| `DOCLING_SERVE_ENABLE_UI` | false | Включить Gradio UI |
| `DOCLING_SERVE_EXTERNAL_MODEL_ENABLED` | false | Включить внешние модели |
| `DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL` | | URL Ollama/vLLM |
| `DOCLING_SERVE_LOG_LEVEL` | INFO | Уровень логирования |
| `DOCLING_SERVE_API_KEY` | | API key для авторизации |

## Версия

**v1.0.0** — см. `VERSION` файл (SemVer).

## API Endpoints

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/v1/convert/source` | POST | Синхронная конвертация по URL |
| `/v1/convert/file` | POST | Синхронная конвертация файла |
| `/v1/convert/source/async` | POST | Асинхронная конвертация по URL |
| `/v1/convert/file/async` | POST | Асинхронная конвертация файла |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness probe |
| `/docs` | GET | Swagger UI |
| `/ui` | GET | Gradio UI |

## Правила агента

- **Grace 2:** `.kilocode/rules/agent-rules.mdc`, skills `mode-architect` → `mode-code` → `mode-debug` → `mode-qa`
- **Пользовательские правила:** `.kilocode/rules/<имя_проекта>.md`

## Changelog

См. `docs/HISTORY.md`