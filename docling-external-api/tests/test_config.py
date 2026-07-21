# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): Config, Settings; TECH(7): pytest]
## @modulecontract
## @purpose Tests for ExternalApiConfig class with standalone service settings.
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, config, settings, ExternalApiConfig, environment variables, standalone

import pytest

from docling_external_api.config import ExternalApiConfig, get_config


# region FUNC_test_docling_serve_url_config [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test docling_serve_url configuration.
## @io None -> None
## @complexity 4
def test_docling_serve_url_config():
    """Test docling_serve_url has correct default."""
    config = ExternalApiConfig()

    assert config.docling_serve_url == "http://localhost:5001"

    print("[IMP:5][test_docling_serve_url_config][PASS] docling_serve_url default OK")
# endregion FUNC_test_docling_serve_url_config


# region FUNC_test_docling_serve_url_from_env [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test docling_serve_url from environment variable.
## @io None -> None
## @complexity 4
def test_docling_serve_url_from_env(monkeypatch):
    """Test loading docling_serve_url from environment."""
    monkeypatch.setenv("DOCLING_SERVE_URL", "http://docling-serve:5001")

    config = ExternalApiConfig()

    assert config.docling_serve_url == "http://docling-serve:5001"

    print("[IMP:5][test_docling_serve_url_from_env][PASS] docling_serve_url from env OK")
# endregion FUNC_test_docling_serve_url_from_env


# region FUNC_test_api_port_config [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test api_port configuration.
## @io None -> None
## @complexity 3
def test_api_port_config():
    """Test api_port has correct default."""
    config = ExternalApiConfig()

    assert config.api_port == 5002

    print("[IMP:4][test_api_port_config][PASS] api_port default OK")
# endregion FUNC_test_api_port_config


# region FUNC_test_api_port_from_env [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test api_port from environment variable.
## @io None -> None
## @complexity 4
def test_api_port_from_env(monkeypatch):
    """Test loading api_port from environment."""
    monkeypatch.setenv("EXTERNAL_API_PORT", "8080")

    config = ExternalApiConfig()

    assert config.api_port == 8080

    print("[IMP:5][test_api_port_from_env][PASS] api_port from env OK")
# endregion FUNC_test_api_port_from_env


# region FUNC_test_get_config_singleton [DOMAIN(5): Testing; CONCEPT(6): Config; TECH(7): pytest]
## @purpose Test get_config returns singleton.
## @io None -> None
## @complexity 4
def test_get_config_singleton(monkeypatch):
    """Test get_config returns cached instance."""
    monkeypatch.setenv("DOCLING_SERVE_URL", "http://test:5001")
    monkeypatch.setenv("EXTERNAL_API_PORT", "9999")

    config1 = get_config()
    config2 = get_config()

    assert config1 is config2
    assert config1.docling_serve_url == "http://test:5001"
    assert config1.api_port == 9999

    print("[IMP:5][test_get_config_singleton][PASS] Singleton pattern OK")
# endregion FUNC_test_get_config_singleton


# region FUNC_test_vlm_config_still_works [DOMAIN(5): Testing; CONCEPT(6): VLM Config; TECH(7): pytest]
## @purpose Test VLM configuration still works.
## @io None -> None
## @complexity 4
def test_vlm_config_still_works():
    """Test VLM config fields are still functional."""
    config = ExternalApiConfig(
        vlm_enabled=True,
        vlm_base_url="https://api.test.com/v1",
        vlm_api_key="sk-test",
        vlm_model="test-model",
    )

    assert config.vlm_enabled is True
    assert config.vlm_base_url == "https://api.test.com/v1"
    assert config.vlm_model == "test-model"

    preset = config.get_vlm_preset()
    assert preset is not None
    assert preset["model"] == "test-model"

    print("[IMP:5][test_vlm_config_still_works][PASS] VLM config works OK")
# endregion FUNC_test_vlm_config_still_works