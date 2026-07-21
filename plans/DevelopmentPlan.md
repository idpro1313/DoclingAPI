# Development Plan: DoclingAPI

**PURPOSE:** Документ-конспект для AI-агентов. Полная документация — `docs/README.md`.

---

## 1. Архитектура (Draft Code Graph)

```xml
<DraftCodeGraph>
  <!-- Main Application -->
  <docling_serve_py FILE="docling-serve/docling_serve/__main__.py" TYPE="CLI">
    <annotation>Точка входа: docling-serve run/dev/rq_worker</annotation>
    <main_FUNC NAME="main" TYPE="ENTRY_POINT"/>
  </docling_serve_py>

  <app_py FILE="docling-serve/docling_serve/app.py" TYPE="FASTAPI">
    <annotation>FastAPI application factory.</annotation>
    <create_app_FUNC NAME="create_app" TYPE="FACTORY"/>
    <process_url_FUNC NAME="process_url" TYPE="ENDPOINT"/>
    <process_file_FUNC NAME="process_file" TYPE="ENDPOINT"/>
  </app_py>

  <!-- Configuration -->
  <settings_py FILE="docling-serve/docling_serve/settings.py" TYPE="CONFIG">
    <DoclingServeSettings_CLASS NAME="DoclingServeSettings" TYPE="SETTINGS"/>
    <external_model_*_FIELDS NAME="external_model_*" TYPE="CONFIG"/>
  </settings_py>

  <!-- External Model API -->
  <convert_options_extender_py FILE="docling-serve/docling_serve/convert_options_extender.py" TYPE="EXTERNAL_MODEL">
    <ExternalModelConfig_CLASS NAME="ExternalModelConfig" TYPE="DATACLASS"/>
    <ExternalModelRegistry_CLASS NAME="ExternalModelRegistry" TYPE="SINGLETON"/>
  </convert_options_extender_py>

  <!-- Docker Deployment -->
  <Dockerfile_FILE FILE="docling-serve/Dockerfile" TYPE="DOCKER">
    <annotation>Multi-stage build: builder + runtime, BuildKit cache</annotation>
  </Dockerfile_FILE>

  <run_docker_sh FILE="docling-serve/run_docker.sh" TYPE="SCRIPT">
    <annotation>Интерактивный скрипт сборки и запуска</annotation>
  </run_docker_sh>
</DraftCodeGraph>
```

---

## 2. Data Flow: Docker Deployment

```
┌─ Builder Stage ─────────────────────────────────────────────┐
│ ▶ COPY pyproject.toml uv.lock                               │
│ → uv venv /app/.venv                                       │
│ → uv sync --frozen --no-dev --no-install-project          │
│ → COPY docling_serve/                                      │
│ → uv sync --frozen --no-dev  ← устанавливает пакет        │
│ → COPY .venv → Runtime                                    │
└────────────────────────────────────────────────────────────┘

┌─ Runtime Stage ───────────────────────────────────────────┐
│ ▶ COPY --from=builder /app/.venv /app/.venv               │
│ → create user docling (uid 1000)                          │
│ → chown -R docling:docling /app                            │
│ → USER docling                                            │
│ → EXPOSE 5001                                             │
│ → CMD ["docling-serve", "run"]                             │
└────────────────────────────────────────────────────────────┘

┌─ Container Execution ─────────────────────────────────────┐
│ ▶ /app/.venv/bin/docling-serve run                         │
│ → create_app() → FastAPI app                              │
│ → lifespan: init orchestrator                           │
│ → uvicorn listening on 0.0.0.0:5001                      │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCLING_SERVE_HOST` | 0.0.0.0 | Bind address |
| `DOCLING_SERVE_PORT` | 5001 | Port |
| `DOCLING_SERVE_ENABLE_UI` | false | Gradio UI |
| `DOCLING_SERVE_EXTERNAL_MODEL_ENABLED` | false | External models |
| `DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL` | | Ollama/vLLM URL |
| `DOCLING_SERVE_LOG_LEVEL` | INFO | Log level |

---

## 4. Acceptance Criteria

- [x] **AC1:** Dockerfile собирает образ с docling_serve пакетом
- [x] **AC2:** `docling-serve run` запускает сервер в контейнере
- [x] **AC3:** Health check проходит на /health
- [x] **AC4:** Gradio UI доступен на /ui (с ENABLE_UI=true)
- [x] **AC5:** External Model API работает с Ollama/vLLM
- [x] **AC6:** BuildKit cache ускоряет повторные сборки
- [x] **AC7:** Non-root пользователь для безопасности
- [ ] **AC8:** Тесты проходят в Docker environment

---

## 5. Troubleshooting

| Error | Solution |
|-------|----------|
| `No module named 'docling_serve'` | Используйте `uv sync --frozen --no-dev` после COPY source |
| flash-attn build failed | Добавьте `--no-extra flash-attn` |
| Slow rebuild | Используйте BuildKit cache mounts |

---

## 6. Related Files

- `docs/README.md` — общая документация
- `docs/HISTORY.md` — журнал изменений
- `AppGraph.xml` — полный граф модулей