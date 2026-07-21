from __future__ import annotations

# region MODULE_CONTRACT [DOMAIN(8): External API Plugin; CONCEPT(7): OpenAI, Integration; TECH(8): docling-serve]
## @modulecontract
## @purpose Позволяет подключать внешние OpenAI-compatible модели (VLM, OCR, Table, Layout, Picture) к docling-serve.
## @scope Plugin для docling-serve с поддержкой external API через env vars или явный вызов setup_external_api().
## @input Environment variables: EXTERNAL_API_*_ENABLED, EXTERNAL_API_*_BASE_URL, EXTERNAL_API_*_API_KEY, EXTERNAL_API_*_MODEL
## @output Preset dict для DoclingConverterManagerConfig или pluggy plugin registration.
## @invariants
## - Оригинальные модели используются если external API не настроен
## - Безопасность: api_key не логируется
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
## @modulemap
## CLASS 8[Configuration] => ExternalApiConfig
## FUNC 9[Integration entry point] => setup_external_api
## FUNC 5[Pluggy entry point] => plugin
## @usecases
## - [setup_external_api]: User (DevOps) → ConfigureExternalModels → DoclingReady
## - [plugin]: System (Pluggy) → RegisterPlugin → PluginAvailable
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: docling, external API, OpenAI-compatible, VLM, OCR, plugin, docling-serve
# STRUCTURE: ▶ Init ┌EXTERNAL_API_* env vars┐ → ○ setup_external_api() → ⚡ Register presets → ⎋ return config

"""
docling-external-api: External API Plugin for docling-serve

Позволяет подключать внешние OpenAI-compatible модели для:
- VLM (Vision-Language Models) - анализ страниц документов
- OCR (Optical Character Recognition) - распознавание текста
- Table Structure - определение структуры таблиц
- Picture Description - описание изображений
- Layout - анализ layout документа

Использование:
    # Вариант 1: Через env vars
    export EXTERNAL_API_VLM_ENABLED=1
    export EXTERNAL_API_VLM_BASE_URL=https://api.openai.com/v1
    export EXTERNAL_API_VLM_API_KEY=sk-...
    python -c "from docling_external_api import setup_external_api; print(setup_external_api())"

    # Вариант 2: Через Python API
    from docling_external_api import setup_external_api, ExternalApiConfig
    config = ExternalApiConfig(vlm_enabled=True, vlm_base_url="...", vlm_api_key="...")
    preset_config = setup_external_api(config)
"""

__version__ = "0.1.0"

from docling_external_api.config import (
    ExternalApiConfig,
    EngineSettings,
    load_config,
)

from docling_external_api.integration import (
    setup_external_api,
    register_plugin,
    plugin,
)

__all__ = [
    "__version__",
    "ExternalApiConfig",
    "EngineSettings",
    "load_config",
    "setup_external_api",
    "register_plugin",
    "plugin",
]