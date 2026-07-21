from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

# region MODULE_CONTRACT [DOMAIN(7): Configuration; CONCEPT(6): Settings, Environment; TECH(9): pydantic-settings]
## @modulecontract
## @purpose Позволяет пользователю подключить внешние OpenAI-compatible API для моделей Docling через env vars или YAML config.
## @scope Конфигурация URL, API key, model selection, timeout для VLM/OCR/Table/Layout моделей.
## @input Environment variables с префиксом EXTERNAL_API_ или YAML/JSON config файл.
## @output Pydantic dataclass с настройками для подключения к external API.
## @links [USES_API(8): pydantic-settings]
## @invariants
## - ExternalApiConfig всегда содержит base_url для активного engine
## - api_key не логируется (security)
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
## @modulemap
## CLASS 8[Configuration settings] => ExternalApiConfig
## CLASS 5[Per-engine settings] => EngineSettings
## FUNC 7[Creates preset dict] => create_vlm_preset
## FUNC 7[Creates preset dict] => create_ocr_preset
## FUNC 7[Creates preset dict] => create_table_preset
## @usecases
## - [ExternalApiConfig]: System (Bootstrap) → LoadConfiguration → SettingsLoaded
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: External API, OpenAI-compatible, configuration, settings, environment variables, docling-serve plugin
# STRUCTURE: ▶ Init ┌EXTERNAL_API_* env vars┐ → ○ ExternalApiConfig.load() → ⚡ Validation → ⊕ presets → ⎋ return settings

_log = logging.getLogger(__name__)


class EngineSettings(BaseSettings):
    """Per-engine settings for external API connection."""

    model_config = SettingsConfigDict(env_prefix="EXTERNAL_API_", extra="allow")

    base_url: str = Field(
        default="",
        description="Base URL for OpenAI-compatible API endpoint"
    )
    api_key: str = Field(
        default="",
        description="API key for authentication"
    )
    model: str = Field(
        default="gpt-4o",
        description="Model name to use"
    )
    timeout: float = Field(
        default=120.0,
        description="Request timeout in seconds"
    )
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in response"
    )
    temperature: float = Field(
        default=0.0,
        description="Sampling temperature"
    )
    enabled: bool = Field(
        default=False,
        description="Enable this engine"
    )

    @model_validator(mode="after")
    def validate_enabled(self) -> "EngineSettings":
        if self.enabled and not self.base_url:
            _log.warning(
                "[IMP:7][ExternalApiConfig][VALIDATE] Engine enabled but no base_url configured"
            )
        return self


# region CLASS_ExternalApiConfig [DOMAIN(7): Configuration; CONCEPT(8): Settings, API; TECH(9): pydantic-settings]
## @purpose Центральный класс конфигурации для всех external API настроек.
## @io None -> ExternalApiConfig
## @complexity 6
class ExternalApiConfig(BaseSettings):
    """Configuration for external OpenAI-compatible API integration with docling-serve."""

    model_config = SettingsConfigDict(
        env_prefix="EXTERNAL_API_",
        env_file=".env",
        env_parse_none_str="",
        extra="allow",
    )

    # VLM settings
    vlm_base_url: str = Field(
        default="",
        description="Base URL for VLM (Vision-Language Model) API"
    )
    vlm_api_key: str = Field(
        default="",
        description="API key for VLM"
    )
    vlm_model: str = Field(
        default="gpt-4o",
        description="VLM model name"
    )
    vlm_enabled: bool = Field(
        default=False,
        description="Enable external VLM API"
    )
    vlm_timeout: float = Field(
        default=120.0,
        description="VLM request timeout"
    )

    # OCR settings
    ocr_base_url: str = Field(
        default="",
        description="Base URL for OCR API"
    )
    ocr_api_key: str = Field(
        default="",
        description="API key for OCR"
    )
    ocr_model: str = Field(
        default="gpt-4o",
        description="OCR model name"
    )
    ocr_enabled: bool = Field(
        default=False,
        description="Enable external OCR API"
    )

    # Table structure settings
    table_base_url: str = Field(
        default="",
        description="Base URL for table structure API"
    )
    table_api_key: str = Field(
        default="",
        description="API key for table structure"
    )
    table_model: str = Field(
        default="gpt-4o",
        description="Table structure model name"
    )
    table_enabled: bool = Field(
        default=False,
        description="Enable external table structure API"
    )

    # Picture description settings
    picture_base_url: str = Field(
        default="",
        description="Base URL for picture description API"
    )
    picture_api_key: str = Field(
        default="",
        description="API key for picture description"
    )
    picture_model: str = Field(
        default="gpt-4o",
        description="Picture description model name"
    )
    picture_enabled: bool = Field(
        default=False,
        description="Enable external picture description API"
    )

    # Layout settings
    layout_base_url: str = Field(
        default="",
        description="Base URL for layout API"
    )
    layout_api_key: str = Field(
        default="",
        description="API key for layout"
    )
    layout_model: str = Field(
        default="gpt-4o",
        description="Layout model name"
    )
    layout_enabled: bool = Field(
        default=False,
        description="Enable external layout API"
    )

    @property
    def is_any_enabled(self) -> bool:
        """Check if any external API is enabled."""
        return any([
            self.vlm_enabled,
            self.ocr_enabled,
            self.table_enabled,
            self.picture_enabled,
            self.layout_enabled,
        ])

    @property
    def enabled_engines(self) -> list[str]:
        """Get list of enabled engine names."""
        engines = []
        if self.vlm_enabled:
            engines.append("vlm")
        if self.ocr_enabled:
            engines.append("ocr")
        if self.table_enabled:
            engines.append("table")
        if self.picture_enabled:
            engines.append("picture_description")
        if self.layout_enabled:
            engines.append("layout")
        return engines

    def get_vlm_preset(self) -> Optional[dict[str, Any]]:
        """Create VLM preset dict for docling-serve custom_vlm_presets."""
        if not self.vlm_enabled:
            return None

        _log.info(
            f"[IMP:7][ExternalApiConfig][GET_VLM_PRESET] Creating VLM preset for model={self.vlm_model}"
        )

        return {
            "url": f"{self.vlm_base_url.rstrip('/')}/chat/completions",
            "api_key": self.vlm_api_key,
            "model": self.vlm_model,
            "timeout": self.vlm_timeout,
            "temperature": 0.0,
            "decode_response": {
                "format": "json",
                "schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                    },
                    "required": ["content"],
                },
            },
        }

    def get_ocr_preset(self) -> Optional[dict[str, Any]]:
        """Create OCR preset dict for docling-serve custom_ocr_presets."""
        if not self.ocr_enabled:
            return None

        _log.info(
            f"[IMP:7][ExternalApiConfig][GET_OCR_PRESET] Creating OCR preset for model={self.ocr_model}"
        )

        return {
            "url": f"{self.ocr_base_url.rstrip('/')}/chat/completions",
            "api_key": self.ocr_api_key,
            "model": self.ocr_model,
            "timeout": 60.0,
        }

    def get_table_preset(self) -> Optional[dict[str, Any]]:
        """Create table structure preset dict for docling-serve custom_table_structure_presets."""
        if not self.table_enabled:
            return None

        _log.info(
            f"[IMP:7][ExternalApiConfig][GET_TABLE_PRESET] Creating table preset for model={self.table_model}"
        )

        return {
            "url": f"{self.table_base_url.rstrip('/')}/chat/completions",
            "api_key": self.table_api_key,
            "model": self.table_model,
            "timeout": 60.0,
        }

    def get_picture_preset(self) -> Optional[dict[str, Any]]:
        """Create picture description preset dict for docling-serve custom_picture_description_presets."""
        if not self.picture_enabled:
            return None

        _log.info(
            f"[IMP:7][ExternalApiConfig][GET_PICTURE_PRESET] Creating picture preset for model={self.picture_model}"
        )

        return {
            "url": f"{self.picture_base_url.rstrip('/')}/chat/completions",
            "api_key": self.picture_api_key,
            "model": self.picture_model,
            "timeout": 60.0,
        }

    def get_all_presets(self) -> dict[str, dict[str, Any]]:
        """Get all configured presets as a dict for direct assignment to docling-serve settings."""
        presets = {}

        vlm_preset = self.get_vlm_preset()
        if vlm_preset:
            presets["vlm"] = vlm_preset

        ocr_preset = self.get_ocr_preset()
        if ocr_preset:
            presets["ocr"] = ocr_preset

        table_preset = self.get_table_preset()
        if table_preset:
            presets["table"] = table_preset

        picture_preset = self.get_picture_preset()
        if picture_preset:
            presets["picture_description"] = picture_preset

        _log.info(
            f"[IMP:7][ExternalApiConfig][GET_ALL_PRESETS] Generated presets for engines: {list(presets.keys())}"
        )

        return presets
# endregion CLASS_ExternalApiConfig


def load_config() -> ExternalApiConfig:
    """Load configuration from environment variables."""
    _log.info("[IMP:6][load_config][INIT] Loading ExternalApiConfig from environment")
    config = ExternalApiConfig()
    _log.info(
        f"[IMP:7][load_config][RESULT] Config loaded, enabled engines: {config.enabled_engines}"
    )
    return config