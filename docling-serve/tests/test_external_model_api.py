"""Tests for external model API configuration in docling-serve."""

import json

import pytest

from docling_serve.convert_options_extender import (
    ExternalModelConfig,
    ExternalModelRegistry,
    build_picture_description_api_config,
    get_external_model_registry,
    init_registry_from_settings,
)
from docling_serve.policy import ServicePolicy, build_service_policy, validate_convert_options
from docling_serve.settings import DoclingServeSettings


class TestExternalModelConfig:
    """Tests for ExternalModelConfig dataclass."""

    def test_create_config(self):
        """Test creating ExternalModelConfig."""
        config = ExternalModelConfig(
            name="ollama",
            base_url="http://localhost:11434/v1",
            api_key="",
            timeout=60.0,
            default_model="llama3.2",
        )
        assert config.name == "ollama"
        assert config.base_url == "http://localhost:11434/v1"
        assert config.default_model == "llama3.2"

    def test_to_api_dict(self):
        """Test converting config to API dict format."""
        config = ExternalModelConfig(
            name="test",
            base_url="http://localhost:11434/v1",
            timeout=30.0,
            default_model="test-model",
        )
        api_dict = config.to_api_dict()

        assert api_dict["url"] == "http://localhost:11434/v1"
        assert api_dict["params"]["model"] == "test-model"
        assert api_dict["timeout"] == 30.0

    def test_to_api_dict_with_override(self):
        """Test model override in to_api_dict."""
        config = ExternalModelConfig(
            name="test",
            base_url="http://localhost:11434/v1",
            default_model="default-model",
        )
        api_dict = config.to_api_dict(model_override="override-model")

        assert api_dict["params"]["model"] == "override-model"

    def test_from_dict_flat(self):
        """Test parsing from flat dict format."""
        data = {
            "base_url": "http://localhost:11434/v1",
            "api_key": "secret",
            "timeout": 45.0,
            "default_model": "my-model",
        }
        config = ExternalModelConfig.from_dict(data, name="flat-test")

        assert config.base_url == "http://localhost:11434/v1"
        assert config.api_key == "secret"
        assert config.timeout == 45.0
        assert config.default_model == "my-model"

    def test_from_dict_nested(self):
        """Test parsing from nested JSON format (docling compatible)."""
        data = {
            "url": "http://localhost:11434/v1/chat/completions",
            "params": {"model": "granite3.2-vision:2b", "temperature": 0.7},
            "timeout": 60,
            "prompt": "Describe this image",
        }
        config = ExternalModelConfig.from_dict(data, name="nested-test")

        assert config.base_url == "http://localhost:11434/v1/chat/completions"
        assert config.default_model == "granite3.2-vision:2b"
        assert config.timeout == 60.0
        assert config.extra_params["temperature"] == 0.7
        assert config.extra_params["prompt"] == "Describe this image"

    def test_to_json_string(self):
        """Test serialization to JSON string."""
        config = ExternalModelConfig(
            name="test",
            base_url="http://localhost:11434/v1",
            default_model="test-model",
        )
        json_str = config.to_json_string()
        parsed = json.loads(json_str)

        assert parsed["url"] == "http://localhost:11434/v1"
        assert parsed["params"]["model"] == "test-model"


class TestExternalModelRegistry:
    """Tests for ExternalModelRegistry singleton."""

    def test_register_and_get_config(self):
        """Test registering and retrieving a model configuration."""
        registry = get_external_model_registry()
        registry.clear()

        config = ExternalModelConfig(name="test-model", base_url="http://test.com")
        registry.register("test-model", config)

        retrieved = registry.get_config("test-model")
        assert retrieved is not None
        assert retrieved.name == "test-model"
        assert retrieved.base_url == "http://test.com"

    def test_get_default_config(self):
        """Test retrieving default configuration."""
        registry = get_external_model_registry()
        registry.clear()

        config = ExternalModelConfig(name="default-model", base_url="http://default.com")
        registry.register("default-model", config, set_as_default=True)

        retrieved = registry.get_config()
        assert retrieved is not None
        assert retrieved.name == "default-model"

    def test_case_insensitive_lookup(self):
        """Test case-insensitive model name lookup."""
        registry = get_external_model_registry()
        registry.clear()

        config = ExternalModelConfig(name="TestModel", base_url="http://test.com")
        registry.register("TestModel", config)

        assert registry.get_config("TESTMODEL") is not None
        assert registry.get_config("testmodel") is not None
        assert registry.get_config("TestModel") is not None

    def test_list_models(self):
        """Test listing all registered models."""
        registry = get_external_model_registry()
        registry.clear()

        registry.register("model1", ExternalModelConfig(name="model1", base_url="http://m1.com"))
        registry.register("model2", ExternalModelConfig(name="model2", base_url="http://m2.com"))

        models = registry.list_models()
        assert len(models) == 2
        assert "model1" in models
        assert "model2" in models

    def test_set_default(self):
        """Test setting default model."""
        registry = get_external_model_registry()
        registry.clear()

        registry.register("model1", ExternalModelConfig(name="model1", base_url="http://m1.com"))
        registry.register("model2", ExternalModelConfig(name="model2", base_url="http://m2.com"))

        registry.set_default("model2")
        assert registry.get_default_name() == "model2"

    def test_build_api_config_with_registry_default(self):
        """Test building API config using registry defaults."""
        registry = get_external_model_registry()
        registry.clear()

        registry.register(
            "ollama",
            ExternalModelConfig(
                name="ollama",
                base_url="http://localhost:11434/v1",
                default_model="llama3.2",
                timeout=60.0,
            ),
            set_as_default=True,
        )

        api_dict = registry.build_api_config(model_name="ollama")
        assert api_dict is not None
        assert api_dict["url"] == "http://localhost:11434/v1"
        assert api_dict["params"]["model"] == "llama3.2"

    def test_build_api_config_merge_request(self):
        """Test merging request config with registry defaults."""
        registry = get_external_model_registry()
        registry.clear()

        registry.register(
            "ollama",
            ExternalModelConfig(
                name="ollama",
                base_url="http://localhost:11434/v1",
                default_model="llama3.2",
                timeout=60.0,
            ),
            set_as_default=True,
        )

        request_config = {"params": {"model": "custom-model"}}
        api_dict = registry.build_api_config(request_config)

        assert api_dict is not None
        assert api_dict["url"] == "http://localhost:11434/v1"
        assert api_dict["params"]["model"] == "custom-model"
        assert api_dict["timeout"] == 60.0

    def test_build_picture_description_api_config(self):
        """Test building picture_description_api JSON config."""
        registry = get_external_model_registry()
        registry.clear()

        registry.register(
            "ollama",
            ExternalModelConfig(
                name="ollama",
                base_url="http://localhost:11434/v1",
                default_model="granite-vision",
                timeout=30.0,
            ),
            set_as_default=True,
        )

        result = build_picture_description_api_config()
        assert result is not None

        parsed = json.loads(result)
        assert parsed["url"] == "http://localhost:11434/v1"
        assert parsed["params"]["model"] == "granite-vision"


class TestSettingsExternalModel:
    """Tests for external model settings in DoclingServeSettings."""

    def test_external_model_settings_defaults(self):
        """Test default values for external model settings."""
        settings = DoclingServeSettings()

        assert settings.external_model_enabled is False
        assert settings.external_model_base_url == ""
        assert settings.external_model_api_key == ""
        assert settings.external_model_timeout == 60.0
        assert settings.external_model_default_model == ""

    def test_external_model_settings_from_env(self, monkeypatch):
        """Test loading external model settings from environment variables."""
        monkeypatch.setenv("DOCLING_SERVE_EXTERNAL_MODEL_ENABLED", "true")
        monkeypatch.setenv("DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL", "http://localhost:11434/v1")
        monkeypatch.setenv("DOCLING_SERVE_EXTERNAL_MODEL_API_KEY", "my-secret-key")
        monkeypatch.setenv("DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT", "120")
        monkeypatch.setenv("DOCLING_SERVE_EXTERNAL_MODEL_DEFAULT_MODEL", "llama3.2-vision")

        settings = DoclingServeSettings()

        assert settings.external_model_enabled is True
        assert settings.external_model_base_url == "http://localhost:11434/v1"
        assert settings.external_model_api_key == "my-secret-key"
        assert settings.external_model_timeout == 120.0
        assert settings.external_model_default_model == "llama3.2-vision"


class TestServicePolicyExternalModels:
    """Tests for external models in ServicePolicy."""

    def test_external_models_enabled_in_policy(self):
        """Test that external_models_enabled is included in ServicePolicy."""
        settings = DoclingServeSettings(external_model_enabled=True)
        policy = build_service_policy(settings)

        assert hasattr(policy, "external_models_enabled")
        assert policy.external_models_enabled is True

    def test_external_models_disabled_by_default(self):
        """Test that external_models_enabled is False by default."""
        settings = DoclingServeSettings()
        policy = build_service_policy(settings)

        assert policy.external_models_enabled is False


class TestInitRegistryFromSettings:
    """Tests for init_registry_from_settings function."""

    def test_init_registry_disabled(self):
        """Test registry initialization when external_model_enabled is False."""
        settings = DoclingServeSettings(external_model_enabled=False)
        registry = get_external_model_registry()
        registry.clear()

        init_registry_from_settings(settings)

        assert len(registry.list_models()) == 0

    def test_init_registry_enabled(self):
        """Test registry initialization when external_model_enabled is True."""
        settings = DoclingServeSettings(
            external_model_enabled=True,
            external_model_base_url="http://localhost:11434/v1",
            external_model_default_model="test-model",
        )
        registry = get_external_model_registry()
        registry.clear()

        init_registry_from_settings(settings)

        models = registry.list_models()
        assert "default" in models

        default_config = registry.get_config("default")
        assert default_config is not None
        assert default_config.base_url == "http://localhost:11434/v1"
        assert default_config.default_model == "test-model"

    def test_init_registry_no_base_url(self):
        """Test registry initialization with empty base_url."""
        settings = DoclingServeSettings(
            external_model_enabled=True,
            external_model_base_url="",
        )
        registry = get_external_model_registry()
        registry.clear()

        init_registry_from_settings(settings)

        assert len(registry.list_models()) == 0


# region FUNC_test_integration_external_model_flow [DOMAIN(7): Testing; CONCEPT(8): Integration; TECH(8): pytest, caplog]
## @purpose Verify end-to-end external model configuration flow with LDD telemetry.
## @uses caplog (pytest fixture), json
## @complexity 6
class TestIntegrationExternalModelFlow:
    """Integration tests for external model API configuration flow."""

    def test_full_flow_settings_to_api_config(self, caplog):
        """Test complete flow from settings to API config generation."""
        import logging
        caplog.set_level(logging.DEBUG, logger="docling_serve.convert_options_extender")

        settings = DoclingServeSettings(
            external_model_enabled=True,
            external_model_base_url="http://localhost:11434/v1",
            external_model_default_model="granite-vision",
            external_model_timeout=45.0,
        )

        registry = get_external_model_registry()
        registry.clear()
        init_registry_from_settings(settings)

        api_config = registry.build_api_config()

        found_init_log = False
        found_build_log = False

        print("\n--- LDD TRAJECTORY (IMP:5-9) ---")
        for record in caplog.records:
            if "[IMP:" in record.message:
                try:
                    imp_level = int(record.message.split("[IMP:")[1].split("]")[0])
                    if imp_level >= 5:
                        print(record.message)
                    if imp_level >= 5 and "init_registry_from_settings" in record.message:
                        found_init_log = True
                    if imp_level >= 5 and "build_api_config" in record.message:
                        found_build_log = True
                except (IndexError, ValueError):
                    continue

        assert api_config is not None, "API config should not be None"
        assert api_config["url"] == "http://localhost:11434/v1"
        assert api_config["params"]["model"] == "granite-vision"
        assert api_config["timeout"] == 45.0

        assert found_init_log, "Expected init_registry_from_settings log at IMP:5+"
# endregion FUNC_test_integration_external_model_flow