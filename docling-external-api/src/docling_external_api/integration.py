from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from docling_external_api.config import ExternalApiConfig, load_config

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from docling_serve.settings import DoclingServeSettings


# region MODULE_CONTRACT [DOMAIN(8): Integration; CONCEPT(7): Plugin, DoclingServe; TECH(9): pluggy]
## @modulecontract
## @purpose Подключить external API plugin к docling-serve без модификации оригинального кода.
## @scope Интеграция через custom_vlm_presets, custom_ocr_presets и другие custom_*_presets.
## @input ExternalApiConfig с настройками подключения.
## @output Модифицированные настройки docling_serve_settings или регистрация pluggy plugin.
## @links [READS_DATA_FROM(7): docling_serve.settings]
## @invariants
## - setup_external_api() вызывается ДО инициализации DoclingConverterManager
## - Оригинальные модели используются если external API не настроен
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
## @modulemap
## FUNC 9[Main integration entry point] => setup_external_api
## FUNC 7[Register pluggy entry point] => register_plugin
## @usecases
## - [setup_external_api]: System (Bootstrap) → IntegrateExternalModels → DoclingExtended
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Integration, plugin, docling-serve, external API, setup, pluggy, custom presets
# STRUCTURE: ▶ Init ┌ExternalApiConfig┐ → ○ Detect mode (manual/pluggy) → ⚡ Register presets → ⎋ return modified_settings


# region FUNC_setup_external_api [DOMAIN(8): Integration; CONCEPT(8): Plugin, Setup; TECH(9): docling-serve]
## @purpose Подключить external API к docling-serve. Возвращает словарь настроек для передачи в DoclingConverterManagerConfig.
## @uses ExternalApiConfig, docling_serve_settings (optional import)
## @io Optional[ExternalApiConfig] -> dict[str, Any]
## @complexity 8
def setup_external_api(config: Optional[ExternalApiConfig] = None) -> dict[str, Any]:
    """Setup external API integration with docling-serve.

    This function configures docling-serve to use external OpenAI-compatible
    APIs for VLM, OCR, Table Structure, Picture Description, and Layout models.

    Args:
        config: Optional ExternalApiConfig. If None, loads from environment.

    Returns:
        Dict with preset configurations for DoclingConverterManagerConfig:
        - custom_vlm_presets
        - allowed_vlm_presets
        - default_vlm_preset
        - custom_ocr_presets
        - custom_table_structure_presets
        - custom_picture_description_presets
        - allow_custom_vlm_config (if any enabled)

    Example:
        ```python
        from docling_external_api import setup_external_api

        preset_config = setup_external_api()
        # Use preset_config in DoclingConverterManagerConfig
        ```
    """
    _log.info("[IMP:7][setup_external_api][INIT] Starting external API setup")

    if config is None:
        _log.debug("[IMP:6][setup_external_api][LOAD_CONFIG] No config provided, loading from env")
        config = load_config()

    if not config.is_any_enabled:
        _log.warning(
            "[IMP:7][setup_external_api][NO_CONFIG] No external APIs enabled. "
            "Set EXTERNAL_API_*_ENABLED=1 and EXTERNAL_API_*_BASE_URL to configure."
        )
        return {}

    _log.info(
        f"[IMP:8][setup_external_api][ENABLED] Setting up external API for: {config.enabled_engines}"
    )

    result: dict[str, Any] = {}

    # VLM configuration
    if config.vlm_enabled:
        vlm_preset_name = "external_api_vlm"
        result["custom_vlm_presets"] = {vlm_preset_name: config.get_vlm_preset()}
        result["allowed_vlm_presets"] = [vlm_preset_name]
        result["default_vlm_preset"] = vlm_preset_name
        result["allow_custom_vlm_config"] = True
        _log.info(f"[IMP:8][setup_external_api][VLM] Configured VLM preset: {vlm_preset_name}")

    # OCR configuration
    if config.ocr_enabled:
        ocr_preset_name = "external_api_ocr"
        if "custom_ocr_presets" not in result:
            result["custom_ocr_presets"] = {}
        result["custom_ocr_presets"][ocr_preset_name] = config.get_ocr_preset()
        _log.info(f"[IMP:8][setup_external_api][OCR] Configured OCR preset: {ocr_preset_name}")

    # Table structure configuration
    if config.table_enabled:
        table_preset_name = "external_api_table"
        if "custom_table_structure_presets" not in result:
            result["custom_table_structure_presets"] = {}
        result["custom_table_structure_presets"][table_preset_name] = config.get_table_preset()
        _log.info(f"[IMP:8][setup_external_api][TABLE] Configured table preset: {table_preset_name}")

    # Picture description configuration
    if config.picture_enabled:
        picture_preset_name = "external_api_picture"
        if "custom_picture_description_presets" not in result:
            result["custom_picture_description_presets"] = {}
        result["custom_picture_description_presets"][picture_preset_name] = config.get_picture_preset()
        _log.info(f"[IMP:8][setup_external_api][PICTURE] Configured picture preset: {picture_preset_name}")

    _log.info(
        f"[IMP:9][setup_external_api][COMPLETE] External API setup complete. "
        f"Configured engines: {config.enabled_engines}"
    )

    return result
# endregion FUNC_setup_external_api


# region FUNC_register_plugin [DOMAIN(6): Plugin; CONCEPT(5): pluggy; TECH(8): setuptools]
## @purpose Зарегистрировать плагин через pluggy entry point (вызывается автоматически).
## @io None -> dict[str, list]
## @complexity 5
def register_plugin() -> dict[str, list]:
    """Pluggy entry point function for docling-external-api plugin.

    This function is registered in pyproject.toml as:
    [project.entry-points."docling"]
    docling_external_api = "docling_external_api.plugin"

    Returns:
        Dict with engine types and their implementations.
    """
    _log.debug("[IMP:5][register_plugin][INIT] Registering docling-external-api plugin")

    return {
        "vlm": [],
        "ocr": [],
        "picture_description": [],
        "table_structure": [],
        "layout": [],
    }
# endregion FUNC_register_plugin


def plugin() -> dict[str, list]:
    """Alias for register_plugin() for pluggy compatibility."""
    return register_plugin()