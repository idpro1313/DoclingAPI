# Docker Deployment Guide

## Быстрый старт

```bash
cd docling-serve
./run_docker.sh --build
```

После запуска:
- API: http://localhost:5001
- Docs: http://localhost:5001/docs
- UI: http://localhost:5001/ui

## Опции run_docker.sh

| Опция | Описание |
|-------|----------|
| `--build` | Пересобрать Docker образ |
| `--external-model` | Включить Ollama/vLLM интеграцию |
| `--verbose` | Подробный вывод сборки |
| `--help` | Показать справку |

## Environment переменные для Docker

```bash
# Основные
DOCLING_SERVE_PORT=5001
DOCLING_SERVE_ENABLE_UI=true
DOCLING_SERVE_LOG_LEVEL=INFO

# External Model API
DOCLING_SERVE_EXTERNAL_MODEL_ENABLED=true
DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL=http://host.docker.internal:11434/v1
DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT=60
DOCLING_SERVE_EXTERNAL_MODEL_DEFAULT_MODEL=granite-vision

# API Key (опционально)
DOCLING_SERVE_API_KEY=your-secret-key
```

## Ручной запуск

```bash
# Сборка
cd docling-serve
docker build -t docling-serve:latest .

# Запуск
docker run -d \
  --name docling-serve \
  --restart unless-stopped \
  -p 5001:5001 \
  -e DOCLING_SERVE_ENABLE_UI=true \
  -v $(pwd)/data:/data \
  -v $(pwd)/scratch:/tmp/docling-scratch \
  docling-serve:latest
```

## Docker Compose

```yaml
services:
  docling:
    build: .
    container_name: docling-serve
    restart: unless-stopped
    ports:
      - "5001:5001"
    environment:
      DOCLING_SERVE_ENABLE_UI: "true"
      DOCLING_SERVE_EXTERNAL_MODEL_ENABLED: "true"
      DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL: "http://ollama:11434/v1"
    volumes:
      - ./data:/data
      - ./scratch:/tmp/docling-scratch

  ollama:
    image: ollama/ollama
    container_name: ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama

volumes:
  ollama-data:
```

## Troubleshooting

### Ошибка: No module named 'docling_serve'

Образ собран без установки пакета. Убедитесь что в Dockerfile:
```dockerfile
COPY docling_serve/ ./docling_serve/
RUN uv sync --frozen --no-dev
```

### Медленная первая сборка

Нормально — скачиваются ML модели (~4GB). Повторные сборки быстрые благодаря BuildKit cache.

### Контейнер падает с OOM

Увеличьте лимиты:
```bash
docker run --memory=8g --cpus=4 ...
```

### Health check fails

Проверьте логи:
```bash
docker logs docling-serve
```

## Volumes

| Volume | Mount | Description |
|--------|-------|-------------|
| `./data` | `/data` | Входные файлы |
| `./scratch` | `/tmp/docling-scratch` | Временные файлы |

## Production checklist

- [ ] Используйте `--build-arg BUILDKIT_INLINE_CACHE=1` для кэширования
- [ ] Установите `DOCLING_SERVE_API_KEY` для авторизации
- [ ] Настройте `DOCLING_SERVE_LOG_LEVEL=WARNING`
- [ ] Ограничьте ресурсы: `--memory`, `--cpus`
- [ ] Настройте мониторинг через `/metrics` endpoint