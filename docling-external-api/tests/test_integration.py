# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): Integration; TECH(7): pytest]
## @modulecontract
## @purpose Tests for integration module (setup_external_api, register_plugin).
## @changes
## LAST_CHANGE: v0.1.0 - Initial creation
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, integration, setup, plugin, docling-serve

import pytest

from docling_external_api.config import ExternalApiConfig
from docling_external_api.integration import setup_external_api, register_plugin, plugin


# region FUNC_test_setup_external_api_no_config [DOMAIN(5): Testing; CONCEPT(6): Integration; TECH(7): pytest]
## @purpose Test setup_external_api returns empty dict when no config.
## @io None -> None
## @complexity 3
def test_setup_external_api_no_config():
    """Test setup_external_api returns empty dict when no engines enabled."""
    result = setup_external_api(ExternalApiConfig())

    assert result == {}
    assert "custom_vlm_presets" not in result

    print("[IMP:4][test_setup_external_api_no_config][PASS] Empty config returns empty dict OK")
# endregion FUNC_test_setup_external_api_no_config


# region FUNC_test_setup_external_api_vlm_only [DOMAIN(5): Testing; CONCEPT(6): Integration; TECH(7): pytest]
## @purpose Test setup_external_api with VLM only.
## @io None -> None
## @complexity 5
def test_setup_external_api_vlm_only():
    """Test setup_external_api configures VLM preset correctly."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1",
        vlm_api_key="sk-test",
        vlm_model="gpt-4o",
    )

    result = setup_external_api(config)

    assert "custom_vlm_presets" in result
    assert "allowed_vlm_presets" in result
    assert "default_vlm_preset" in result
    assert "allow_custom_vlm_config" in result

    assert result["default_vlm_preset"] == "external_api_vlm"
    assert "external_api_vlm" in result["allowed_vlm_presets"]
    assert "external_api_vlm" in result["custom_vlm_presets"]

    preset = result["custom_vlm_presets"]["external_api_vlm"]
    assert preset["url"] == "https://api.openai.com/v1/chat/completions"
    assert preset["api_key"] == "sk-test"
    assert preset["model"] == "gpt-4o"

    print("[IMP:6][test_setup_external_api_vlm_only][PASS] VLM only setup OK")
# endregion FUNC_test_setup_external_api_vlm_only


# region FUNC_test_setup_external_api_multiple_engines [DOMAIN(5): Testing; CONCEPT(6): Integration; TECH(7): pytest]
## @purpose Test setup_external_api with multiple engines.
## @io None -> None
## @complexity 6
def test_setup_external_api_multiple_engines():
    """Test setup_external_api configures multiple engines correctly."""
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

    result = setup_external_api(config)

    assert "custom_vlm_presets" in result
    assert "custom_ocr_presets" in result
    assert "custom_table_structure_presets" in result

    assert "external_api_vlm" in result["custom_vlm_presets"]
    assert "external_api_ocr" in result["custom_ocr_presets"]
    assert "external_api_table" in result["custom_table_structure_presets"]

    print("[IMP:6][test_setup_external_api_multiple_engines][PASS] Multiple engines setup OK")
# endregion FUNC_test_setup_external_api_multiple_engines


# region FUNC_test_setup_external_api_auto_load [DOMAIN(5): Testing; CONCEPT(6): Integration; TECH(7): pytest]
## @purpose Test setup_external_api auto-loads config from env.
## @io None -> None
## @complexity 4
def test_setup_external_api_auto_load(monkeypatch):
    """Test setup_external_api loads config from env when not provided."""
    monkeypatch.setenv("EXTERNAL_API_VLM_ENABLED", "1")
    monkeypatch.setenv("EXTERNAL_API_VLM_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("EXTERNAL_API_VLM_API_KEY", "sk-env-key")

    result = setup_external_api()

    assert "custom_vlm_presets" in result
    preset = result["custom_vlm_presets"]["external_api_vlm"]
    assert preset["api_key"] == "sk-env-key"

    print("[IMP:5][test_setup_external_api_auto_load][PASS] Auto-load from env OK")
# endregion FUNC_test_setup_external_api_auto_load


# region FUNC_test_register_plugin [DOMAIN(5): Testing; CONCEPT(6): Plugin; TECH(7): pytest]
## @purpose Test pluggy plugin registration function.
## @io None -> None
## @complexity 3
def test_register_plugin():
    """Test pluggy entry point function."""
    result = register_plugin()

    assert isinstance(result, dict)
    assert "vlm" in result
    assert "ocr" in result
    assert "picture_description" in result
    assert "table_structure" in result
    assert "layout" in result

    print("[IMP:4][test_register_plugin][PASS] Plugin registration OK")
# endregion FUNC_test_register_plugin


# region FUNC_test_plugin_alias [DOMAIN(5): Testing; CONCEPT(6): Plugin; TECH(7): pytest]
## @purpose Test plugin() is alias for register_plugin().
## @io None -> None
## @complexity 3
def test_plugin_alias():
    """Test plugin() is alias for register_plugin()."""
    assert plugin() == register_plugin()

    print("[IMP:3][test_plugin_alias][PASS] Plugin alias OK")
# endregion FUNC_test_plugin_alias


# region FUNC_test_preset_contains_required_fields [DOMAIN(5): Testing; CONCEPT(6): Preset; TECH(7): pytest]
## @purpose Test that generated presets contain required docling-serve fields.
## @io None -> None
## @complexity 5
def test_preset_contains_required_fields():
    """Test VLM preset has required fields for docling-serve."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.openai.com/v1",
        vlm_api_key="sk-test",
        vlm_model="gpt-4o",
    )

    result = setup_external_api(config)
    preset = result["custom_vlm_presets"]["external_api_vlm"]

    required_fields = ["url", "api_key", "model", "timeout"]
    for field in required_fields:
        assert field in preset, f"Required field '{field}' missing from preset"

    print("[IMP:5][test_preset_contains_required_fields][PASS] Required fields OK")
# endregion FUNC_test_preset_contains_required_fields