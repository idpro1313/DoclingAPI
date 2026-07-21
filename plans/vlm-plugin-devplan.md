# Development Plan: VLM Plugin for docling-serve

**PURPOSE:** Интеграция внешнего VLM через plugin-систему docling. Плагин загружается при сборке docling-serve из исходников.

**VERSION:** 0.5.0
**STATUS:** PLANNING
**UPDATED:** 2026-07-21

---

## 1. Анализ существующего кода

### 1.1 Docling-serve settings.py
```python
# Ключевые настройки для VLM:
allow_custom_vlm_config: bool = False  # Нужно включить
custom_vlm_presets: dict[str, Any] = Field(default_factory=dict)
default_vlm_preset: str = "granite_docling"
allowed_vlm_presets: Optional[list[str]] = None
allowed_vlm_engines: Optional[list[str]] = None

# Plugin поддержка:
allow_external_plugins: bool = False  # Нужно включить
```

### 1.2 Plugin Discovery
```
docling.models.factories.base_factory - Загружает плагины
Registered picture descriptions: ['picture_description_vlm_engine', 'vlm', 'api']
```

---

## 2. Варианты реализации

### Вариант A: Custom VLM Engine Plugin
**Суть:** Создать custom VLM engine в `docling-serve/` который реализует интерфейс docling для внешних VLM.

```python
# docling-serve/docling_serve/vlm_engines/external_vlm.py
class ExternalVLMEngine(BaseReaderCallback):
    def __init__(self, url: str, api_key: str, model: str):
        self.url = url
        self.api_key = api_key
        self.model = model

    async def process(self, image: Image) -> str:
        # Вызов внешнего VLM API
```

**Плюсы:** Интегрируется в pipeline, работает внутри docling-serve
**Минусы:** Требует изменений в docling-serve код

### Вариант B: External API VLM Engine
**Суть:** Использовать `api` engine с настройками из `custom_vlm_presets`.

Уже поддерживается `vlm` engine типа `api`:
```
Registered picture descriptions: ['picture_description_vlm_engine', 'vlm', 'api']
```

---

### 1. Draft Code Graph

```xml
<DraftCodeGraph>
  <docker_compose_yml FILE="docling-external-api/docker-compose.yml" TYPE="CONFIG">
    <annotation>Docker compose с local docling-serve</annotation>
    <docker_compose_docling_serve_SERVICE NAME="docling-serve" TYPE="SERVICE">
      <annotation>Local build из docling-serve/</annotation>
      <env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG VAR="DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG" TYPE="ENV_VAR">
        <annotation>Enable custom VLM configuration</annotation>
      </env_DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG>
      <env_DOCLING_SERVE_CUSTOM_VLM_PRESETS VAR="DOCLING_SERVE_CUSTOM_VLM_PRESETS" TYPE="ENV_VAR">
        <annotation>JSON с external VLM preset</annotation>
      </env_DOCLING_SERVE_CUSTOM_VLM_PRESETS>
    </docker_compose_docling_serve_SERVICE>
  </docker_compose_yml>
</DraftCodeGraph>
```

---

### 2. Step-by-step Data Flow

1.  **Step 1:** Docker compose собирает docling-serve из `docling-serve/` локально
2.  **Step 2:** docling-serve читает `DOCLING_SERVE_ALLOW_CUSTOM_VLM_CONFIG=true`
3.  **Step 3:** docling-serve парсит `DOCLING_SERVE_CUSTOM_VLM_PRESETS` JSON
4.  **Step 4:** При конвертации используется external VLM через `api` engine
5.  **Step 5:** Результат возвращается клиенту сразу с VLM данными

---

### 3. Acceptance Criteria

- [ ] **AC-VLM-PLUGIN-1:** docling-serve собирается из local source (docling-serve/)
- [ ] **AC-VLM-PLUGIN-2:** VLM конфигурация через ENV variables читается корректно
- [ ] **AC-VLM-PLUGIN-3:** VLM вызывается автоматически при обработке документа
- [ ] **AC-VLM-PLUGIN-4:** docling-external-api получает результат с VLM данными

---

## 3. TODO для Code фазы

- [ ] Обновить docker-compose.yml для build из local source
- [ ] Создать Dockerfile для local docling-serve сборки
- [ ] Добавить ENV variables для VLM конфигурации
- [ ] Протестировать end-to-end
- [ ] Удалить post-processing vlm_handler.py если VLM интегрирован

---

## 4. Структура файлов после изменений

```
docling-external-api/
├── docker-compose.yml          # Будет ссылаться на local docling-serve build
└── Dockerfile                   # Unchanged

docling-serve/                   # Оригинальный код (НЕ изменяется)
├── Containerfile               # Для сборки образа
├── docling_serve/
│   └── settings.py             # Настройки с allow_custom_vlm_config
└── ...

build/                          # Собранные артефакты
├── docling-serve.Dockerfile
└── ...
```

---

**BRANCH:** feature/vlm-plugin

**NEXT:** Запустить Code mode для реализации.