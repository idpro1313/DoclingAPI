# Development Plan: docling-external-api Plugin

**PURPOSE:** Создать отдельный пакет-плагин `docling-external-api`, который расширяет `original/docling-serve/` поддержкой внешних OpenAI-compatible API. Оригинальный код НЕ изменяется.

---

## 0. Архитектура проекта

```
DoclingAPI/
├── original/docling-serve/     # Оригинал (НЕ ТРОГАЕМ)
├── docling-external-api/       # НАШ ПЛАГИН (создаём)
│   ├── src/docling_external_api/
│   ├── tests/
│   └── pyproject.toml
├── plans/
│   └── DevelopmentPlan.md      # Этот документ
└── work/                        # Артефакты агента
```

---

## 1. Исследование: Что ЕСТЬ в оригинале

### Подтверждено в `original/docling-serve/`:

| Компонент | Файл | Тип | Статус |
|-----------|------|-----|--------|
| `custom_vlm_presets` | `settings.py:333` | `dict[str, Any]` | ✅ ЕСТЬ |
| `allowed_vlm_presets` | `settings.py:332` | `Optional[list[str]]` | ✅ ЕСТЬ |
| `default_vlm_preset` | `settings.py:331` | `str` | ✅ ЕСТЬ |
| `custom_picture_description_presets` | `settings.py:339` | `dict[str, Any]` | ✅ ЕСТЬ |
| `custom_table_structure_presets` | `settings.py:358` | `dict[str, Any]` | ✅ ЕСТЬ |
| `allow_custom_vlm_config` | `settings.py:133` | `bool` | ✅ ЕСТЬ |
| `custom_ocr_presets` | `settings.py:371` | `dict[str, Any]` | ✅ ЕСТЬ |

### Точки подключения (в `orchestrator_factory.py`):
```python
DoclingConverterManagerConfig(
    ...
    custom_vlm_presets=docling_serve_settings.custom_vlm_presets,
    allowed_vlm_presets=docling_serve_settings.allowed_vlm_presets,
    custom_picture_description_presets=docling_serve_settings.custom_picture_description_presets,
    custom_table_structure_presets=docling_serve_settings.custom_table_structure_presets,
    custom_ocr_presets=docling_serve_settings.custom_ocr_presets,
    ...
)
```

### Ограничения оригинала
- Оригинальный код в `original/` не модифицируется
- Плагин подключается через env vars или явный вызов `setup_external_api()`
- Обратная совместимость: при отсутствии конфигурации работают оригинальные модели

### Формат preset (из `test_env_parsing.py`)
```python
custom_vlm_presets = {
    "my_preset": {
        "engine": "openai",
        "url": "https://api.openai.com/v1/chat/completions",
        ...
    }
}
```

### Неизвестно (нужно проверить в docling-jobkit)
- Точная структура preset dict — какие ключи ожидает `DoclingConverterManager`?
- `ApiVlmModel` — есть ли в docling-jobkit или только в базовом docling?
- Какой формат ответа ожидается от external API?

---

## 1. Критерии успеха

1. **Изоляция:** Оригинальный код `original/docling-serve/` не изменяется
2. **Полнота VLM:** Поддержка VLM через встроенный `ApiVlmModel` с OpenAI-compatible API
3. **Расширяемость:** Архитектура для поддержки OCR, Layout, Table Structure через factory substitution
4. **Конфигурируемость:** Настройка через env vars и config file
5. **Обратная совместимость:** Оригинальные модели работают при отсутствии внешнего API

---

## 2. Выбранная архитектура: VLM + Factory Substitution

### Концепция
1. **VLM:** Использовать встроенный `ApiVlmModel` с `ApiVlmOptions` — не требует monkey-patching
2. **Factory Substitution:** Расширяемые адаптеры для OCR/Layout/Table Structure через подмену factory

### Архитектура VLM (фаза 1)
```
EXTERNAL_MODEL_BASE_URL + API_KEY 
  → docling_serve_settings.custom_vlm_presets
  → DoclingConverterManager 
  → ApiVlmModel 
  → OpenAI-compatible API
```

### Архитектура Factory Substitution (фаза 2)
```
EXTERNAL_OCR_BASE_URL + API_KEY
  → ExternalOcrFactory 
  → BaseOcrModel subclass 
  → OpenAI-compatible API / Vision endpoint
```

### Контекст встраивания
- Подключение происходит через `docling_serve_settings` в `orchestrator_factory.py`
- `custom_vlm_presets` уже поддерживается в DoclingConverterManager
- Factory substitution для OCR/Layout/Table — через `pluggy` entry point или runtime patching

### 2. Draft Code Graph

```xml
<DraftCodeGraph>
  <docling_api_plugin_py FILE="src/docling_api_plugin/__init__.py" TYPE="PACKAGE_INIT">
    <annotation>Главный экспорт плагина для подключения внешних моделей.</annotation>
    <Exports>
      <Export NAME="DoclingAPIClient" TYPE="CLASS" />
      <Export NAME="setup_external_models" TYPE="FUNCTION" />
      <Export NAME="ExternalModelConfig" TYPE="DATACLASS" />
    </Exports>
  </docling_api_plugin_py>

  <client_py FILE="src/docling_api_plugin/client.py" TYPE="MODULE">
    <annotation>HTTP-клиент для взаимодействия с OpenAI-compatible API.</annotation>
    <ExternalModelClient_CLASS NAME="ExternalModelClient" TYPE="CLASS">
      <annotation>Асинхронный клиент для отправки запросов к внешнему API.</annotation>
      <ExternalModelClient___init___METHOD NAME="__init__" TYPE="METHOD">
        <annotation>Инициализация клиента с конфигурацией.</annotation>
      </ExternalModelClient___init___METHOD>
      <ExternalModelClient_chat_COMPLETE_METHOD NAME="chat_complete" TYPE="METHOD">
        <annotation>Отправка chat completion запроса.</annotation>
      </ExternalModelClient_chat_COMPLETE_METHOD>
      <ExternalModelClient_embeddings_METHOD NAME="embeddings" TYPE="METHOD">
        <annotation>Получение эмбеддингов для текста.</annotation>
      </ExternalModelClient_chat_COMPLETE_METHOD>
    </ExternalModelClient_CLASS>
  </client_py>

  <adapters_py FILE="src/docling_api_plugin/adapters.py" TYPE="MODULE">
    <annotation>Адаптеры для подключения внешних моделей к каждому типу задач Docling.</annotation>
    <BaseAdapter_CLASS NAME="BaseAdapter" TYPE="CLASS">
      <annotation>Базовый класс адаптера модели.</annotation>
      <BaseAdapter_process_METHOD NAME="process" TYPE="METHOD" />
    </BaseAdapter_CLASS>
    
    <VLMLikeAdapter_CLASS NAME="VLMLikeAdapter" TYPE="CLASS" IS_SUBCLASS_OF="BaseAdapter">
      <annotation>Адаптер для VLM-like моделей (страницы документов).</annotation>
      <CrossLinks>
        <Link TARGET="client_py_ExternalModelClient_chat_COMPLETE_METHOD" TYPE="USES_METHOD" />
      </CrossLinks>
    </VLMLikeAdapter_CLASS>
    
    <OCRAdapter_CLASS NAME="OCRAdapter" TYPE="CLASS" IS_SUBCLASS_OF="BaseAdapter">
      <annotation>Адаптер для OCR моделей.</annotation>
    </OCRAdapter_CLASS>
    
    <TableStructureAdapter_CLASS NAME="TableStructureAdapter" TYPE="CLASS" IS_SUBCLASS_OF="BaseAdapter">
      <annotation>Адаптер для table structure моделей.</annotation>
    </TableStructureAdapter_CLASS>
    
    <LayoutAdapter_CLASS NAME="LayoutAdapter" TYPE="CLASS" IS_SUBCLASS_OF="BaseAdapter">
      <annotation>Адаптер для layout моделей.</annotation>
    </LayoutAdapter_CLASS>
  </adapters_py>

  <factory_py FILE="src/docling_api_plugin/factory.py" TYPE="MODULE">
    <annotation>Фабрика моделей с поддержкой factory substitution.</annotation>
    <ExternalModelFactory_CLASS NAME="ExternalModelFactory" TYPE="CLASS">
      <annotation>Фабрика для создания адаптеров внешних моделей.</annotation>
      <ExternalModelFactory_get_model_METHOD NAME="get_model" TYPE="METHOD">
        <annotation>Получить модель по типу и preset.</annotation>
        <CrossLinks>
          <Link TARGET="adapters_py_*Adapter_CLASS" TYPE="CREATES_ADAPTER" />
        </CrossLinks>
      </ExternalModelFactory_get_model_METHOD>
    </ExternalModelFactory_CLASS>
  </factory_py>

  <patcher_py FILE="src/docling_api_plugin/patcher.py" TYPE="MODULE">
    <annotation>Механизм monkey-patching для подмены фабричных функций.</annotation>
    <ModelPatcher_CLASS NAME="ModelPatcher" TYPE="CLASS">
      <annotation>Контекстный менеджер для безопасного применения патчей.</annotation>
      <ModelPatcher_apply_METHOD NAME="apply" TYPE="METHOD" />
      <ModelPatcher_restore_METHOD NAME="restore" TYPE="METHOD" />
    </ModelPatcher_CLASS>
  </patcher_py>

  <config_py FILE="src/docling_api_plugin/config.py" TYPE="MODULE">
    <annotation>Конфигурация плагина через Pydantic Settings.</annotation>
    <ExternalModelConfig_CLASS NAME="ExternalModelConfig" TYPE="CLASS">
      <annotation>Настройки подключения к внешнему API.</annotation>
      <ExternalModelConfig_base_url_FIELD NAME="base_url" TYPE="FIELD" />
      <ExternalModelConfig_api_key_FIELD NAME="api_key" TYPE="FIELD" />
      <ExternalModelConfig_enabled_engines_FIELD NAME="enabled_engines" TYPE="FIELD" />
    </ExternalModelConfig_CLASS>
  </config_py>

  <integration_py FILE="src/docling_api_plugin/integration.py" TYPE="MODULE">
    <annotation>Интеграция с FastAPI/FastMCP для docling-serve.</annotation>
    <setup_external_models_FUNCTION NAME="setup_external_models" TYPE="FUNCTION">
      <annotation>Главная точка входа для активации плагина.</annotation>
      <CrossLinks>
        <Link TARGET="patcher_py_ModelPatcher_apply_METHOD" TYPE="CALLS_METHOD" />
      </CrossLinks>
    </setup_external_models_FUNCTION>
  </integration_py>
</DraftCodeGraph>
```

---

## 3. Draft Code Graph (VLM Plugin)

```xml
<DraftCodeGraph>
  <vlm_plugin_py FILE="src/docling_external_api/__init__.py" TYPE="PACKAGE_INIT">
    <annotation>Главный экспорт плагина для подключения внешних VLM моделей.</annotation>
    <Exports>
      <Export NAME="setup_external_vlm" TYPE="FUNCTION" />
      <Export NAME="ExternalVlmConfig" TYPE="CLASS" />
    </Exports>
  </vlm_plugin_py>

  <config_py FILE="src/docling_external_api/config.py" TYPE="MODULE">
    <annotation>Конфигурация VLM плагина через Pydantic Settings.</annotation>
    <ExternalVlmConfig_CLASS NAME="ExternalVlmConfig" TYPE="CLASS">
      <annotation>Настройки подключения к внешнему OpenAI-compatible API для VLM.</annotation>
      <ExternalVlmConfig_base_url_FIELD NAME="base_url" TYPE="FIELD" />
      <ExternalVlmConfig_api_key_FIELD NAME="api_key" TYPE="FIELD" />
      <ExternalVlmConfig_model_FIELD NAME="model" TYPE="FIELD" />
      <ExternalVlmConfig_timeout_FIELD NAME="timeout" TYPE="FIELD" />
    </ExternalVlmConfig_CLASS>
  </config_py>

  <presets_py FILE="src/docling_external_api/presets.py" TYPE="MODULE">
    <annotation>Preset-конфигурации для DoclingConverterManager.</annotation>
    <OpenAICompatibleVlmPreset_FUNCTION NAME="OpenAICompatibleVlmPreset" TYPE="FUNCTION">
      <annotation>Создает ApiVlmOptions для OpenAI-compatible API.</annotation>
      <CrossLinks>
        <Link TARGET="config_py_ExternalVlmConfig_CLASS" TYPE="USES_CONFIG" />
      </CrossLinks>
    </OpenAICompatibleVlmPreset_FUNCTION>
  </presets_py>

  <integration_py FILE="src/docling_external_api/integration.py" TYPE="MODULE">
    <annotation>Интеграция с docling-serve.</annotation>
    <setup_external_vlm_FUNCTION NAME="setup_external_vlm" TYPE="FUNCTION">
      <annotation>Главная точка входа для активации плагина.</annotation>
      <CrossLinks>
        <Link TARGET="presets_py_OpenAICompatibleVlmPreset_FUNCTION" TYPE="CALLS_FUNCTION" />
        <Link TARGET="orchestrator_factory_py" TYPE="CALLS" />
      </CrossLinks>
    </setup_external_vlm_FUNCTION>
  </integration_py>
</DraftCodeGraph>
```

---

## 4. Step-by-step Data Flow

### Конфигурация (Bootstrap)
```
1. Пользователь задает EXTERNAL_VLM_BASE_URL, EXTERNAL_VLM_API_KEY, EXTERNAL_VLM_MODEL
2. ExternalVlmConfig загружает конфигурацию из env/config
3. setup_external_vlm() вызывается при инициализации
```

### Регистрация VLM Preset
```
1. setup_external_vlm() создает ApiVlmOptions из конфига
2. OpenAICompatibleVlmPreset() регистрирует preset в custom_vlm_presets
3. preset_name добавляется в allowed_vlm_presets
4. default_vlm_preset устанавливается на новый preset
```

### Обработка документа (Runtime)
```
1. Docling получает задачу конвертации
2. DoclingConverterManager выбирает VLM preset
3. При preset = "openai_compatible" создается ApiVlmModel
4. ApiVlmModel отправляет image + prompt в external API
5. Результат парсится в VlmPrediction и прикрепляется к page
```

---

## 5. Acceptance Criteria

- [ ] **AC-1:** Плагин подключается без изменения `original/docling-serve/`
- [ ] **AC-2:** VLM inference перенаправляется на OpenAI-compatible API
- [ ] **AC-3:** Конфигурация через env vars: `EXTERNAL_VLM_BASE_URL`, `EXTERNAL_VLM_API_KEY`, `EXTERNAL_VLM_MODEL`
- [ ] **AC-4:** Fallback на оригинальные модели при отсутствии конфигурации
- [ ] **AC-5:** Логирование всех запросов к внешнему API (LDD format)
- [ ] **AC-6:** Unit-тесты с mock HTTP server
- [ ] **AC-7:** Integration тест с реальным или mock API

---

## 6. Структура проекта

```
src/docling_external_api/
├── __init__.py           # Главный экспорт: setup_external_vlm, ExternalVlmConfig
├── config.py             # Pydantic Settings для конфигурации
├── presets.py            # Preset-функции для ApiVlmOptions
└── integration.py        # Интеграция с docling-serve

tests/
├── test_config.py
├── test_presets.py
└── test_integration.py

plans/
└── DevelopmentPlan.md    # Этот документ
```

---

## 7. Зависимости

```toml
# docling-external-api/pyproject.toml
dependencies = [
    "pydantic>=2.10.0",        # Конфигурация (уже есть в docling-serve)
    "pydantic-settings>=2.4.0", # ENV vars (уже есть в docling-serve)
]
```

---

## 8. Структура пакета docling-external-api

```
docling-external-api/
├── pyproject.toml              # Entry point: docling = docling_external_api.plugin
├── src/docling_external_api/
│   ├── __init__.py            # setup_external_api, ExternalApiConfig
│   ├── config.py              # ExternalApiConfig (Pydantic Settings)
│   ├── vlm_presets.py         # Preset-функции для ApiVlmOptions
│   ├── ocr_adapter.py          # BaseOcrModel subclass для OCR
│   ├── table_adapter.py       # Table structure adapter
│   └── integration.py         # setup_external_api()
└── tests/
    ├── test_config.py
    ├── test_vlm_presets.py
    └── test_integration.py
```

---

## 9. TODO для Code фазы

- [x] Создать структуру `docling-external-api/` с pyproject.toml
- [x] Реализовать `config.py` с ExternalApiConfig (Pydantic Settings)
- [x] Реализовать `integration.py` с setup_external_api()
- [x] Создать `__init__.py` с публичным API и pluggy entry point
- [x] Написать unit-тесты (test_config.py, test_integration.py)
- [x] Подготовить test_guide.md для QA
- [x] Создать Dockerfile с multi-stage build
- [x] Создать docker-compose.yaml с default config
- [x] Создать docker-entrypoint.sh для plugin activation
- [ ] Провести QA тестирование

### Планы на будущее (фаза 2):
- [ ] Реализовать ocr_adapter.py с BaseOcrModel subclass
- [ ] Реализовать table_adapter.py с table structure adapter
- [ ] Добавить integration тесты с mock HTTP server

---

## 10. Реализованные файлы

```
docling-external-api/
├── pyproject.toml              # Entry point: docling = docling_external_api.plugin
├── README.md
├── Dockerfile                   # Multi-stage build with plugin
├── docker-compose.yaml          # Docker Compose configuration
├── docker-entrypoint.sh         # Entrypoint script for plugin activation
├── src/docling_external_api/
│   ├── __init__.py            # setup_external_api, ExternalApiConfig, plugin
│   ├── config.py              # ExternalApiConfig (Pydantic Settings)
│   ├── integration.py         # setup_external_api(), register_plugin()
│   └── plugin.py              # pluggy entry point
└── tests/
    ├── conftest.py            # pytest fixtures
    ├── test_config.py         # 8 tests for ExternalApiConfig
    ├── test_integration.py    # 7 tests for integration
    └── test_guide.md          # QA guide
```

---

## 11. Docker Deployment

### Быстрый старт

```bash
cd docling-external-api

# Сборка и запуск
docker compose up --build

# Проверка
curl http://localhost:5001/health
```

### Конфигурация по умолчанию

| Параметр | Значение |
|----------|----------|
| VLM Base URL | `http://192.168.101.15:8111/v1` |
| VLM Model | `minimax-m2.7` |
| Port | `5001` |
| UI | Enabled |

### Переменные окружения

| Variable | Description | Default |
|----------|-------------|---------|
| `EXTERNAL_API_VLM_ENABLED` | Enable external VLM | `1` |
| `EXTERNAL_API_VLM_BASE_URL` | VLM API base URL | `http://192.168.101.15:8111/v1` |
| `EXTERNAL_API_VLM_MODEL` | VLM model name | `minimax-m2.7` |
| `EXTERNAL_API_VLM_API_KEY` | API key | (empty) |
| `EXTERNAL_API_OCR_ENABLED` | Enable external OCR | `0` |
| `DOCLING_SERVE_ENABLE_REMOTE_SERVICES` | Enable remote API | `true` |
| `DOCLING_SERVE_LOAD_MODELS_AT_BOOT` | Load local models | `false` |

### Структура Dockerfile

1. `mimalloc` — Build mimalloc library
2. `docling-base` — Base OS layer
3. `docling-serve-base` — Clone and install docling-serve
4. `docling-external-api-plugin` — Install plugin
5. `runtime` — Final image with entrypoint

### Entrypoint

`docker-entrypoint.sh` автоматически:
1. Проверяет настройки external API
2. Загружает конфигурацию через `setup_external_api()`
3. Применяет preset configuration к `DoclingServeSettings`
4. Запускает `docling-serve run`

---

**STATUS:** IMPLEMENTED - Docker deployment ready
**VERSION:** 0.2.0
**CREATED:** 2026-07-21
**UPDATED:** 2026-07-21