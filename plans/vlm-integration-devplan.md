# Development Plan: VLM Integration with docling-serve (Вариант A: ENV-based)

**PURPOSE:** Интеграция внешнего VLM (Vision Language Model) в docling-serve через environment variables. Docling-serve будет вызывать external VLM автоматически во время обработки документа.

**VERSION:** 0.4.0
**STATUS:** PLANNING → APPROVED
**UPDATED:** 2026-07-21

---

## 1. Целевая архитектура (TO-BE)

```
┌─────────────────┐    ┌──────────────────────────────────┐    ┌─────────────┐
│  Client Request │───▶│         docling-serve            │───▶│  External   │
└─────────────────┘    │  ┌────────────────────────────┐  │    │  VLM API    │
                       │  │ Document Processing        │  │    │ (minimax,   │
                       │  │  - OCR                     │  │    │  openai)    │
                       │  │  - Layout Analysis         │  │◀───│             │
                       │  │  - Table Structure         │  │    └─────────────┘
                       │  │  - VLM ◀─── ENV config     │  │
                       │  └────────────────────────────┘  │
                       └──────────────────────────────────┘
```

---

### 1. Draft Code Graph

```xml
<DraftCodeGraph>
  <docker_compose_yml FILE="docling-external-api/docker-compose.yml" TYPE="CONFIG">
    <annotation>Docker compose with docling-serve VLM env vars</annotation>
    <docker_compose_docling_serve_SERVICE NAME="docling-serve" TYPE="SERVICE">
      <annotation>Official docling-serve with integrated VLM config</annotation>
      <env_DOCLING_SERVE_ENABLE_REMOTE_SERVICES VAR="DOCLING_SERVE_ENABLE_REMOTE_SERVICES" TYPE="ENV_VAR">
        <annotation>Enable remote services (VLM, embeddings)</annotation>
      </env_DOCLING_SERVE_ENABLE_REMOTE_SERVICES>
      <env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG VAR="DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG" TYPE="ENV_VAR">
        <annotation>Allow custom VLM configuration</annotation>
      </env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG>
      <env_DOCLING_SERVE_CUSTOM_VLM_PRESETS VAR="DOCLING_SERVE_CUSTOM_VLM_PRESETS" TYPE="ENV_VAR">
        <annotation>JSON preset with external_vlm configuration</annotation>
      </env_DOCLING_SERVE_CUSTOM_VLM_PRESETS>
      <env_DOCLING_SERVE_DEFAULT_VLM_PRESET VAR="DOCLING_SERVE_DEFAULT_VLM_PRESET" TYPE="ENV_VAR">
        <annotation>Default VLM preset name</annotation>
      </env_DOCLING_SERVE_DEFAULT_VLM_PRESET>
    </docker_compose_docling_serve_SERVICE>
  </docker_compose_yml>
</DraftCodeGraph>
```

---

### 2. Step-by-step Data Flow

1.  **Step 1:** Docker compose запускает docling-serve с env variables для VLM
2.  **Step 2:** docling-serve инициализирует remote VLM на основе `DOCLING_SERVE_CUSTOM_VLM_PRESETS`
3.  **Step 3:** Client отправляет POST /v1/convert/source в docling-external-api
4.  **Step 4:** docling-external-api проксирует запрос в docling-serve
5.  **Step 5:** docling-serve вызывает external VLM API автоматически
6.  **Step 6:** VLM результаты интегрируются в document result
7.  **Step 7:** docling-external-api возвращает результат клиенту (без post-processing)

---

### 3. Acceptance Criteria

- [ ] **AC-VLM-1:** docling-serve использует external VLM для обработки документов
- [ ] **AC-VLM-2:** VLM конфигурация передаётся через environment variables
- [ ] **AC-VLM-3:** docling-external-api получает результат сразу с VLM данными
- [ ] **AC-VLM-4:** Один запрос = полный результат с VLM (без двухфазной обработки)
- [ ] **AC-VLM-5:** Fault isolation: VLM ошибки не ломают docling-serve

---

## 2. Environment Variables для docling-serve

### Обязательные переменные

| Variable | Value | Description |
|----------|-------|-------------|
| `DOCLING_SERVE_ENABLE_REMOTE_SERVICES` | `true` | Включить remote services (VLM, embeddings) |
| `DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG` | `true` | Разрешить custom VLM presets |
| `DOCLING_SERVE_CUSTOM_VLM_PRESETS` | JSON string | Custom VLM preset definition |
| `DOCLING_SERVE_DEFAULT_VLM_PRESET` | `external_vlm` | Default preset name |

### Пример JSON для DOCLING_SERVE_CUSTOM_VLM_PRESETS

```json
{
  "presets": {
    "external_vlm": {
      "engine": "openai",
      "url": "http://192.168.101.15:8111/v1",
      "model": "minimax-m2.7",
      "api_key": "optional-key",
      "max_tokens": 4096,
      "temperature": 0.0
    }
  }
}
```

---

## 3. Изменения в docker-compose.yml

```yaml
services:
  docling-serve:
    image: quay.io/docling-project/docling-serve:latest
    ports:
      - "5001:5001"
    environment:
      - DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false
      - DOCLING_SERVE_ENABLE_UI=true
      - DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true
      - DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG=true
      - DOCLING_SERVE_DEFAULT_VLM_PRESET=external_vlm
      - DOCLING_SERVE_CUSTOM_VLM_PRESETS={"presets":{"external_vlm":{"engine":"openai","url":"http://192.168.101.15:8111/v1","model":"minimax-m2.7","max_tokens":4096,"temperature":0.0}}}
    volumes:
      - docling-models:/app/.cache/docling/models
```

---

## 4. TODO для Code фазы

- [ ] Обновить docker-compose.yml с VLM env variables
- [ ] Удалить VLM env variables из docling-external-api секции (они больше не нужны)
- [ ] Упростить vlm_handler.py (или удалить если не нужен)
- [ ] Протестировать VLM integration end-to-end
- [ ] Проверить что docling-serve корректно вызывает external VLM

---

## 5. Риски и ограничения

| Риск | Вероятность | Mitigation |
|------|-------------|------------|
| docling-serve версия не поддерживает custom VLM | Средняя | Проверить версию, fallback на post-processing |
| External VLM недоступен | Низкая | Fault isolation, graceful error handling |
| JSON в env variable слишком большой | Низкая | Использовать file mount для JSON config |

---

**BRANCH:** feature/vlm-integration