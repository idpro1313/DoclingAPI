# Development Plan: Hybrid VLM Integration for docling-serve

**PURPOSE:** Гибридная архитектура — MiniMax M2.7 (text API) для OCR/Layout/Table + DeepSeek-OCR-2 (vision API) для Picture Description.

**VERSION:** 0.6.0
**STATUS:** APPROVED
**UPDATED:** 2026-07-22

---

## 1. Целевая архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clients                                  │
│                   (POST /v1/convert/source и др.)                │
└───────────────────────────────────┬─────────────────────────────┘
                                    │ HTTP :5001
                                    ▼
┌───────────────────────────────────────────────────────────────────┐
│           docling-serve (LOCAL BUILD)                             │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  MiniMax M2.7 (TEXT API - http://192.168.101.15:8111/v1)   │  │
│  │   - OCR → text extraction from images                      │  │
│  │   - Layout → document structure analysis                   │  │
│  │   - Table Structure → table parsing                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  DeepSeek-OCR-2 (VISION API)                               │  │
│  │   - Picture Description → image analysis & description     │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────┬───────────────────────────────┘
                                    │
          ┌─────────────────────────┴─────────────────────────┐
          │                                                   │
          ▼                                                   ▼
┌─────────────────────────┐                  ┌─────────────────────────────────┐
│  MiniMax M2.7 API        │                  │  DeepSeek-OCR-2 API             │
│  http://192.168.101.15   │                  │  foundation-models.api.cloud.ru │
│  :8111/v1                │                  │  :443                           │
│  No Auth                 │                  │  Bearer Token Auth               │
└─────────────────────────┘                  └─────────────────────────────────┘
```

**Убрано:** docling-external-api — не нужен

---

### 1. Draft Code Graph

```xml
<DraftCodeGraph>
  <docker_compose_yml FILE="docker-compose.yml" TYPE="CONFIG">
    <annotation>Root docker-compose with local docling-serve + hybrid VLM config</annotation>
    <docker_compose_docling_serve_SERVICE NAME="docling-serve" TYPE="SERVICE">
      <annotation>Local build из docling-serve/</annotation>
      <env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG VAR="DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG" TYPE="ENV_VAR">
        <annotation>Enable custom VLM config for OCR/Layout/Table</annotation>
      </env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG>
      <env_DOCLING_SERVE_ALLOW_CUSTOM_PICTURE_DESCRIPTION_CONFIG VAR="DOCLING_SERVE_ALLOW_CUSTOM_PICTURE_DESCRIPTION_CONFIG" TYPE="ENV_VAR">
        <annotation>Enable custom picture description VLM</annotation>
      </env_DOCLING_SERVE_ALLOW_CUSTOM_PICTURE_DESCRIPTION_CONFIG>
    </docker_compose_docling_serve_SERVICE>
  </docker_compose_yml>
</DraftCodeGraph>
```

---

### 2. Step-by-step Data Flow

1.  **Step 1:** Docker compose собирает docling-serve из `docling-serve/`
2.  **Step 2:** docling-serve читает ENV variables для VLM configurations
3.  **Step 3:** OCR → MiniMax M2.7 (text extraction from document images)
4.  **Step 4:** Layout → MiniMax M2.7 (structure analysis)
5.  **Step 5:** Table Structure → MiniMax M2.7 (table parsing)
6.  **Step 6:** Picture Description → DeepSeek-OCR-2 (image description)
7.  **Step 7:** Результат возвращается клиенту

---

### 3. Acceptance Criteria

- [ ] **AC-1:** docling-serve собирается из local source (docling-serve/)
- [ ] **AC-2:** OCR, Layout, Table используют MiniMax M2.7
- [ ] **AC-3:** Picture Description использует DeepSeek-OCR-2
- [ ] **AC-4:** VLM конфигурация через ENV variables
- [ ] **AC-5:** docling-external-api убран
- [ ] **AC-6:** Health check и UI работают

---

## 2. External API Configuration

### MiniMax M2.7 (Text API) - OCR, Layout, Table

| Parameter | Value |
|-----------|-------|
| URL | `http://192.168.101.15:8111/v1/chat/completions` |
| Model | `minimax-m2.7` |
| Auth | None |

### DeepSeek-OCR-2 (Vision API) - Picture Description

| Parameter | Value |
|-----------|-------|
| URL | `https://foundation-models.api.cloud.ru/v1/chat/completions` |
| Model | `deepseek-ai/DeepSeek-OCR-2` |
| Auth | Bearer API Key |
| API Key | `N2Y2MWJkMjAtNGE5OC00MjMwLWI2MTMtNGE4Y2E2OWIzMjU2.dc8bb7f1049fc3b9eb66e5a73740f0e6` |

---

## 3. Required ENV Variables

```bash
# MiniMax M2.7 для OCR/Layout/Table
DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG=true
DOCLING_SERVE_CUSTOM_VLM_PRESETS={"presets":{"minimax_m27":{"engine":"openai","url":"http://192.168.101.15:8111/v1","model":"minimax-m2.7","max_tokens":4096,"temperature":0.0}}}
DOCLING_SERVE_DEFAULT_VLM_PRESET=minimax_m27

# DeepSeek-OCR-2 для Picture Description
DOCLING_SERVE_ALLOW_CUSTOM_PICTURE_DESCRIPTION_CONFIG=true
DOCLING_SERVE_CUSTOM_PICTURE_DESCRIPTION_PRESETS={"presets":{"deepseek_ocr":{"engine":"openai","url":"https://foundation-models.api.cloud.ru/v1","api_key":"N2Y2MWJkMjAtNGE5OC00MjMwLWI2MTMtNGE4Y2E2OWIzMjU2.dc8bb7f1049fc3b9eb66e5a73740f0e6","model":"deepseek-ai/DeepSeek-OCR-2","max_tokens":4096,"temperature":0.0}}}
DOCLING_SERVE_DEFAULT_PICTURE_DESCRIPTION_PRESET=deepseek_ocr
```

---

## 4. Docker Configuration

### docker-compose.yml (root)

```yaml
services:
  docling-serve:
    build:
      context: ./docling-serve
      dockerfile: Containerfile
    container_name: docling-serve
    ports:
      - "5001:5001"
    environment:
      - DOCLING_SERVE_LOAD_MODELS_AT_BOOT=false
      - DOCLING_SERVE_ENABLE_UI=true
      - DOCLING_SERVE_ENABLE_REMOTE_SERVICES=true
      # MiniMax M2.7 для OCR/Layout/Table
      - DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG=true
      - DOCLING_SERVE_DEFAULT_VLM_PRESET=minimax_m27
      - 'DOCLING_SERVE_CUSTOM_VLM_PRESETS={"presets":{"minimax_m27":{"engine":"openai","url":"http://192.168.101.15:8111/v1","model":"minimax-m2.7","max_tokens":4096,"temperature":0.0}}}'
      # DeepSeek-OCR-2 для Picture Description
      - DOCLING_SERVE_ALLOW_CUSTOM_PICTURE_DESCRIPTION_CONFIG=true
      - DOCLING_SERVE_DEFAULT_PICTURE_DESCRIPTION_PRESET=deepseek_ocr
      - 'DOCLING_SERVE_CUSTOM_PICTURE_DESCRIPTION_PRESETS={"presets":{"deepseek_ocr":{"engine":"openai","url":"https://foundation-models.api.cloud.ru/v1","api_key":"N2Y2MWJkMjAtNGE5OC00MjMwLWI2MTMtNGE4Y2E2OWIzMjU2.dc8bb7f1049fc3b9eb66e5a73740f0e6","model":"deepseek-ai/DeepSeek-OCR-2","max_tokens":4096,"temperature":0.0}}}'
    volumes:
      - docling-models:/app/.cache/docling/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  docling-models:
```

---

## 5. Files to Remove

```
docling-external-api/           → REMOVE
run-docker.sh                  → REMOVE
docling-external-api/docker-compose.yml → REMOVE
```

---

## 6. TODO для Code фазы

- [ ] Создать root docker-compose.yml с local docling-serve build
- [ ] Проверить Containerfile в docling-serve/
- [ ] Добавить ENV variables для MiniMax M2.7 (OCR/Layout/Table)
- [ ] Добавить ENV variables для DeepSeek-OCR-2 (Picture Description)
- [ ] Удалить docling-external-api/ папку
- [ ] Удалить run-docker.sh
- [ ] Протестировать end-to-end конвертацию
- [ ] Обновить docs/HISTORY.md

---

**BRANCH:** feature/hybrid-vlm-integration