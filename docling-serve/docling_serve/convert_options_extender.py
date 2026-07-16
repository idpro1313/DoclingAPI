# region MODULE_CONTRACT [DOMAIN(7): Configuration; CONCEPT(8): ExternalModels, ModelRegistry; TECH(8): Pydantic, Dataclass]

## @modulecontract
## @purpose Registry system for managing named external model API configurations (vLLM, Ollama, OpenAI-compatible endpoints).
## @scope Model configuration storage, retrieval, merging with request options.
## @input Named model configurations, request options, server defaults.
## @output ExternalModelConfig with merged API parameters; validated registry entries.
## @links [USES_API(6): json, logging]
## @invariants
## - Registry is a singleton accessible via get_external_model_registry()
## - Model names are case-insensitive
## - Default model is used when request doesn't specify one
## @rationale
## Q: Why a registry instead of direct settings usage?^^
## A: Allows multiple named model configurations, supports per-request model selection, and enables dynamic model updates.
## @changes
## LAST_CHANGE: [v1.0.0 – Initial creation of external model registry system.]
## @modulemap
## CLASS 8[Registry for named model configurations] => ExternalModelRegistry
## CLASS 6[Single model endpoint configuration] => ExternalModelConfig
## FUNC 7[Get singleton registry instance] => get_external_model_registry
## FUNC 6[Build API config dict from registry] => build_api_config
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: External model, API, vLLM, Ollama, OpenAI, registry, configuration, picture_description_api
# STRUCTURE: ▶ Request + ServerDefaults → ○ Registry lookup → ◇ Merge config → ⊕ Build API dict → ⟦Docling pipeline⟧ → ⎋ result

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

_log = logging.getLogger(__name__)


# region CLASS_ExternalModelConfig [DOMAIN(6): Configuration; CONCEPT(7): ExternalModel; TECH(6): dataclass]
## @purpose Lightweight configuration for a single external model API endpoint.
## @io Input: model name, base_url, api_key, timeout, options -> Output: ExternalModelConfig instance
## @complexity 4
@dataclass(frozen=True)
class ExternalModelConfig:
    """Configuration for a single external model API endpoint.

    STRUCTURE: ⚡ [name, base_url, api_key, timeout] → ○ validate → ⎋ ExternalModelConfig

    Example JSON format compatible with existing picture_description_api:
    {
        "url": "http://localhost:11434/v1/chat/completions",
        "params": {"model": "llama3.2-vision"},
        "timeout": 60,
        "prompt": "Describe this image..."
    }
    """

    name: str
    base_url: str = ""
    api_key: str = ""
    timeout: float = 60.0
    default_model: str = ""
    extra_params: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self, model_override: Optional[str] = None) -> dict[str, Any]:
        """Convert to dictionary format expected by docling pipeline API.

        STRUCTURE: ◇ [config fields] → ○ Build url + params → ⎋ return api_dict
        """
        model = model_override or self.default_model
        return {
            "url": self.base_url,
            "params": {"model": model, **self.extra_params},
            "timeout": self.timeout,
            "api_key": self.api_key if self.api_key else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], name: str = "default") -> "ExternalModelConfig":
        """Parse from dictionary, supporting both flat and nested formats.

        STRUCTURE: ⚡ [dict] → ○ Detect format → ◇ Parse url/params/timeout → ⎋ ExternalModelConfig
        """
        url = data.get("url", data.get("base_url", ""))
        timeout = data.get("timeout", 60.0)
        api_key = data.get("api_key", data.get("api-key", ""))

        extra_params = {}
        model = ""
        params = data.get("params", {})
        if isinstance(params, dict):
            model = params.get("model", "")
            extra_params = {k: v for k, v in params.items() if k != "model"}

        prompt = data.get("prompt", "")
        if prompt:
            extra_params["prompt"] = prompt

        return cls(
            name=name,
            base_url=url,
            api_key=api_key,
            timeout=timeout,
            default_model=model,
            extra_params=extra_params,
        )

    def to_json_string(self) -> str:
        """Serialize to JSON string for docling pipeline compatibility."""
        result = {
            "url": self.base_url,
            "params": {"model": self.default_model, **self.extra_params},
            "timeout": self.timeout,
        }
        if self.api_key:
            result["api_key"] = self.api_key
        return json.dumps(result)
# endregion CLASS_ExternalModelConfig


# region CLASS_ExternalModelRegistry [DOMAIN(7): Configuration; CONCEPT(8): ModelRegistry, Singleton; TECH(7): dict]
## @purpose Singleton registry for managing named external model configurations.
## @io Input: model configs -> Output: lookup by name, merge with defaults
## @complexity 6
class ExternalModelRegistry:
    """Registry for managing multiple named external model configurations.

    STRUCTURE: ⚡ [models: dict] → ○ register/lookup/get_config → ⎋ ExternalModelConfig | None

    Usage:
        registry = get_external_model_registry()
        registry.register("ollama", ExternalModelConfig(name="ollama", base_url="http://localhost:11434/v1"))
        config = registry.get_config("ollama")
    """

    def __init__(self):
        self._models: dict[str, ExternalModelConfig] = {}
        self._default_name: Optional[str] = None
        _log.debug("[IMP:4][ExternalModelRegistry][INIT] Registry initialized [STATUS]")

    def register(
        self,
        name: str,
        config: ExternalModelConfig,
        set_as_default: bool = False,
    ) -> None:
        """Register a new external model configuration.

        STRUCTURE: ◇ [name, config] → ○ Store in _models → ⎋ return None
        """
        name_lower = name.lower()
        self._models[name_lower] = config
        if set_as_default or self._default_name is None:
            self._default_name = name_lower
        _log.info(
            f"[IMP:5][ExternalModelRegistry][REGISTER] Registered model '{name}' "
            f"(default={name_lower == self._default_name}) [STATUS]"
        )

    def get_config(self, name: Optional[str] = None) -> Optional[ExternalModelConfig]:
        """Retrieve configuration for a named model or default.

        STRUCTURE: ◇ [name] → ○ Lookup in _models → ⎋ ExternalModelConfig | None
        """
        lookup_name = (name or self._default_name or "").lower()
        if not lookup_name:
            _log.debug("[IMP:5][ExternalModelRegistry][GET_CONFIG] No name provided, returning None [STATUS]")
            return None

        config = self._models.get(lookup_name)
        if config is None:
            _log.warning(
                f"[IMP:6][ExternalModelRegistry][GET_CONFIG] Model '{lookup_name}' not found in registry [WARN]"
            )
        return config

    def list_models(self) -> list[str]:
        """List all registered model names."""
        return list(self._models.keys())

    def get_default_name(self) -> Optional[str]:
        """Get the name of the default model."""
        return self._default_name

    def set_default(self, name: str) -> bool:
        """Set the default model by name. Returns True if successful."""
        name_lower = name.lower()
        if name_lower not in self._models:
            _log.warning(
                f"[IMP:6][ExternalModelRegistry][SET_DEFAULT] Cannot set default to '{name}': not in registry [WARN]"
            )
            return False
        self._default_name = name_lower
        _log.info(f"[IMP:5][ExternalModelRegistry][SET_DEFAULT] Default model set to '{name}' [STATUS]")
        return True

    def clear(self) -> None:
        """Clear all registered models."""
        self._models.clear()
        self._default_name = None
        _log.info("[IMP:5][ExternalModelRegistry][CLEAR] Registry cleared [STATUS]")

    def build_api_config(
        self,
        request_api_config: Optional[dict[str, Any]] = None,
        model_name: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Build complete API configuration merging registry defaults with request overrides.

        STRUCTURE: ⚡ [request_config, model_name] → ○ Get registry config → ◇ Merge with request → ⎋ api_dict

        Priority: request_api_config > registry default > server defaults
        """
        base_config = self.get_config(model_name)

        if request_api_config:
            _log.debug(
                f"[IMP:5][ExternalModelRegistry][BUILD_API_CONFIG] Merging request config with registry [FLOW]"
            )
            if base_config:
                merged = ExternalModelConfig.from_dict(request_api_config, name=base_config.name)
                merged = ExternalModelConfig(
                    name=base_config.name,
                    base_url=merged.base_url or base_config.base_url,
                    api_key=merged.api_key or base_config.api_key,
                    timeout=merged.timeout or base_config.timeout,
                    default_model=merged.default_model or base_config.default_model,
                    extra_params={**base_config.extra_params, **merged.extra_params},
                )
                return merged.to_api_dict()
            return ExternalModelConfig.from_dict(request_api_config).to_api_dict()

        if base_config:
            _log.debug(
                f"[IMP:5][ExternalModelRegistry][BUILD_API_CONFIG] Using registry config for '{base_config.name}' [FLOW]"
            )
            return base_config.to_api_dict()

        _log.debug("[IMP:5][ExternalModelRegistry][BUILD_API_CONFIG] No config available [FLOW]")
        return None
# endregion CLASS_ExternalModelRegistry


# Singleton instance
_registry: Optional[ExternalModelRegistry] = None


# region FUNC_get_external_model_registry [DOMAIN(6): Configuration; CONCEPT(7): Singleton; TECH(6): module]
## @purpose Get the singleton ExternalModelRegistry instance.
## @io None -> ExternalModelRegistry
## @complexity 3
def get_external_model_registry() -> ExternalModelRegistry:
    """Return the singleton ExternalModelRegistry instance.

    STRUCTURE: ○ Check _registry → 〈_registry ? T〉 → ⎋ return _registry
    """
    global _registry
    if _registry is None:
        _registry = ExternalModelRegistry()
        _log.info("[IMP:5][get_external_model_registry][INIT] Created new registry singleton [STATUS]")
    return _registry
# endregion FUNC_get_external_model_registry


# region FUNC_init_registry_from_settings [DOMAIN(6): Configuration; CONCEPT(6): Settings; TECH(6): settings]
## @purpose Initialize the registry from DoclingServeSettings.
## @io settings -> ExternalModelRegistry
## @complexity 4
def init_registry_from_settings(settings: "DoclingServeSettings") -> None:
    """Initialize the external model registry from settings configuration.

    STRUCTURE: ⚡ [settings] → ○ Check external_model_enabled → ◇ Create default config → ⎋ register
    """
    if not settings.external_model_enabled:
        _log.debug("[IMP:5][init_registry_from_settings][SKIP] External models disabled [STATUS]")
        return

    if not settings.external_model_base_url:
        _log.warning("[IMP:6][init_registry_from_settings][WARN] external_model_base_url not set [WARN]")
        return

    registry = get_external_model_registry()
    default_config = ExternalModelConfig(
        name="default",
        base_url=settings.external_model_base_url,
        api_key=settings.external_model_api_key,
        timeout=settings.external_model_timeout,
        default_model=settings.external_model_default_model,
    )
    registry.register("default", default_config, set_as_default=True)

    _log.info(
        f"[IMP:5][init_registry_from_settings][INIT] Registered default model: "
        f"url={settings.external_model_base_url}, model={settings.external_model_default_model} [STATUS]"
    )
# endregion FUNC_init_registry_from_settings


# region FUNC_build_picture_description_api_config [DOMAIN(6): API; CONCEPT(6): PictureDescription; TECH(6): Merge]
## @purpose Build picture_description_api compatible JSON config from registry.
## @io request_config, model_name -> JSON string for docling
## @complexity 4
def build_picture_description_api_config(
    request_api_config: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Optional[str]:
    """Build picture_description_api JSON string using registry defaults.

    STRUCTURE: ◇ [request_str, model_name] → ○ Parse request → ◇ Merge with registry → ⎋ JSON string

    Accepts request_api_config as JSON string (existing format) and returns JSON string.
    """
    registry = get_external_model_registry()

    request_dict = None
    if request_api_config:
        try:
            request_dict = json.loads(request_api_config)
        except json.JSONDecodeError:
            _log.warning(f"[IMP:6][build_picture_description_api_config][PARSE] Invalid JSON in request [WARN]")
            return request_api_config

    api_dict = registry.build_api_config(request_dict, model_name)
    if api_dict:
        return json.dumps(api_dict)
    return None
# endregion FUNC_build_picture_description_api_config