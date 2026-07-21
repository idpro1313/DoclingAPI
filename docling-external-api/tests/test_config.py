# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): Config, Settings; TECH(7): pytest]
## @modulecontract
## @purpose Tests for ExternalApiConfig and EngineSettings classes.
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, config, settings, ExternalApiConfig, environment variables

import os
import pytest

from docling_external_api.config import ExternalApiConfig, load_config


# region FUNC_test_external_api_config_default [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test default ExternalApiConfig values.
## @io None -> None
## @complexity 3
def test_external_api_config_default():
    """Test default configuration values."""
    config = ExternalApiConfig()

    assert config.vlm_enabled is False
    assert config.ocr_enabled is False
    assert config.table_enabled is False
    assert config.picture_enabled is False
    assert config.layout_enabled is False
    assert config.is_any_enabled is False
    assert config.enabled_engines == []

    print("[IMP:5][test_external_api_config_default][PASS] Default config OK")
# endregion FUNC_test_external_api_config_default


# region FUNC_test_external_api_config_from_env [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test loading config from environment variables.
## @io None -> None
## @complexity 4
def test_external_api_config_from_env(monkeypatch):
    """Test loading VLM config from environment variables."""
    monkeypatch.setenv("EXTERNAL_API_VLM_ENABLED", "1")
    monkeypatch.setenv("EXTERNAL_API_VLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("EXTERNAL_API_VLM_API_KEY", "sk-test-key")
    monkeypatch.setenv("EXTERNAL_API_VLM_MODEL", "gpt-4o")

    config = ExternalApiConfig()

    assert config.vlm_enabled is True
    assert config.vlm_base_url == "https://api.openai.com/v1"
    assert config.vlm_api_key == "sk-test-key"
    assert config.vlm_model == "gpt-4o"
    assert config.is_any_enabled is True
    assert "vlm" in config.enabled_engines

    print("[IMP:6][test_external_api_config_from_env][PASS] VLM config from env OK")
# endregion FUNC_test_external_api_config_from_env


# region FUNC_test_get_vlm_preset [DOMAIN(5): Testing; CONCEPT(6): Preset; TECH(7): pytest]
## @purpose Test VLM preset generation.
## @io None -> None
## @complexity 5
def test_get_vlm_preset():
    """Test VLM preset dict generation."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1",
        vlm_api_key="sk-test-key",
        vlm_model="gpt-4o",
        vlm_timeout=120.0,
    )

    preset = config.get_vlm_preset()

    assert preset is not None
    assert preset["url"] == "https://api.openai.com/v1/chat/completions"
    assert preset["api_key"] == "sk-test-key"
    assert preset["model"] == "gpt-4o"
    assert preset["timeout"] == 120.0
    assert preset["temperature"] == 0.0

    print("[IMP:6][test_get_vlm_preset][PASS] VLM preset generation OK")
# endregion FUNC_test_get_vlm_preset


# region FUNC_test_get_vlm_preset_disabled [DOMAIN(5): Testing; CONCEPT(6): Preset; TECH(7): pytest]
## @purpose Test VLM preset returns None when disabled.
## @io None -> None
## @complexity 3
def test_get_vlm_preset_disabled():
    """Test VLM preset returns None when VLM is disabled."""
    config = ExternalApiConfig(vlm_enabled=False)

    preset = config.get_vlm_preset()

    assert preset is None

    print("[IMP:4][test_get_vlm_preset_disabled][PASS] Disabled VLM returns None OK")
# endregion FUNC_test_get_vlm_preset_disabled


# region FUNC_test_get_all_presets [DOMAIN(5): Testing; CONCEPT(6): Presets; TECH(7): pytest]
## @purpose Test getting all configured presets.
## @io None -> None
## @complexity 5
def test_get_all_presets():
    """Test getting all presets at once."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1",
        vlm_api_key="sk-test-key",
        ocr_enabled=True,
        ocr_base_url="https://api.openai.com/v1",
        ocr_api_key="sk-test-key",
    )

    presets = config.get_all_presets()

    assert "vlm" in presets
    assert "ocr" in presets
    assert "table" not in presets
    assert "picture_description" not in presets

    print("[IMP:6][test_get_all_presets][PASS] All presets generation OK")
# endregion FUNC_test_get_all_presets


# region FUNC_test_url_trailing_slash [DOMAIN(5): Testing; CONCEPT(6): URL; TECH(7): pytest]
## @purpose Test URL trailing slash handling.
## @io None -> None
## @complexity 3
def test_url_trailing_slash_handling():
    """Test that trailing slashes in base URLs are handled correctly."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1/",
        vlm_api_key="sk-test-key",
    )

    preset = config.get_vlm_preset()

    assert preset["url"] == "https://api.openai.com/v1/chat/completions"
    assert "v1/" not in preset["url"].rstrip("/").split("/")[-2]

    print("[IMP:4][test_url_trailing_slash][PASS] URL trailing slash handling OK")
# endregion FUNC_test_url_trailing_slash


# region FUNC_test_load_config [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test load_config convenience function.
## @io None -> None
## @complexity 3
def test_load_config(monkeypatch):
    """Test load_config convenience function."""
    monkeypatch.setenv("EXTERNAL_API_VLM_ENABLED", "1")
    monkeypatch.setenv("EXTERNAL_API_VLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("EXTERNAL_API_VLM_API_KEY", "sk-test")

    config = load_config()

    assert isinstance(config, ExternalApiConfig)
    assert config.vlm_enabled is True
    assert config.vlm_base_url == "https://api.openai.com/v1"

    print("[IMP:5][test_load_config][PASS] load_config function OK")
# endregion FUNC_test_load_config


# region FUNC_test_multiple_engines [DOMAIN(5): Testing; CONCEPT(6): Multiple; TECH(7): pytest]
## @purpose Test enabling multiple engines.
## @io None -> None
## @complexity 5
def test_multiple_engines():
    """Test enabling VLM, OCR and Table at the same time."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1",
        vlm_api_key="sk-test",
        ocr_enabled=True,
        ocr_base_url="https://api.openai.com/v1",
        ocr_api_key="sk-test",
        table_enabled=True,
        table_base_url="https://api.openai.com/v1",
        table_api_key="sk-test",
    )

    assert config.is_any_enabled is True
    assert len(config.enabled_engines) == 3
    assert set(config.enabled_engines) == {"vlm", "ocr", "table"}

    presets = config.get_all_presets()
    assert len(presets) == 3

    print("[IMP:6][test_multiple_engines][PASS] Multiple engines enabled OK")
# endregion FUNC_test_multiple_engines