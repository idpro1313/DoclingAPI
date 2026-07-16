# Test Guide: External Model API Configuration

## Overview

This document describes the testing strategy for the external model API configuration feature in docling-serve. The feature enables VLM/LLM models via OpenAI-compatible API endpoints (vLLM, Ollama, etc.).

## Files Under Test

| File | Purpose |
|------|---------|
| `docling_serve/settings.py` | External model configuration settings |
| `docling_serve/policy.py` | Service policy validation |
| `docling_serve/convert_options_extender.py` | Model registry and API config builder |
| `tests/test_external_model_api.py` | Unit and integration tests |

## Test Structure

### Test Classes

1. **TestExternalModelConfig** — Tests for `ExternalModelConfig` dataclass
   - `test_create_config` — Basic config creation
   - `test_to_api_dict` — Conversion to API dict format
   - `test_to_api_dict_with_override` — Model override in to_api_dict
   - `test_from_dict_flat` — Parsing flat dict format
   - `test_from_dict_nested` — Parsing nested JSON format (docling compatible)
   - `test_to_json_string` — Serialization to JSON string

2. **TestExternalModelRegistry** — Tests for `ExternalModelRegistry` singleton
   - `test_register_and_get_config` — Register and retrieve model config
   - `test_get_default_config` — Retrieve default configuration
   - `test_case_insensitive_lookup` — Case-insensitive model name lookup
   - `test_list_models` — List all registered models
   - `test_set_default` — Set default model
   - `test_build_api_config_with_registry_default` — Build API config using registry defaults
   - `test_build_api_config_merge_request` — Merge request config with registry defaults
   - `test_build_picture_description_api_config` — Build picture_description_api JSON config

3. **TestSettingsExternalModel** — Tests for external model settings
   - `test_external_model_settings_defaults` — Default values for settings
   - `test_external_model_settings_from_env` — Loading from environment variables

4. **TestServicePolicyExternalModels** — Tests for ServicePolicy
   - `test_external_models_enabled_in_policy` — Policy includes external_models_enabled
   - `test_external_models_disabled_by_default` — External models disabled by default

5. **TestInitRegistryFromSettings** — Tests for init_registry_from_settings function
   - `test_init_registry_disabled` — Registry init when external_model_enabled=False
   - `test_init_registry_enabled` — Registry init when external_model_enabled=True
   - `test_init_registry_no_base_url` — Registry init with empty base_url

6. **TestIntegrationExternalModelFlow** — Integration tests
   - `test_full_flow_settings_to_api_config` — End-to-end flow with LDD telemetry

## Expected LDD Log Markers

### IMP:5-6 (Flow/Status)
- `[IMP:5][ExternalModelRegistry][INIT]` — Registry initialized
- `[IMP:5][ExternalModelRegistry][REGISTER]` — Model registered
- `[IMP:5][ExternalModelRegistry][CLEAR]` — Registry cleared
- `[IMP:5][init_registry_from_settings][INIT]` — Default model registered
- `[IMP:6][init_registry_from_settings][WARN]` — Warning (no base_url)

### IMP:5 (Flow)
- `[IMP:5][ExternalModelRegistry][BUILD_API_CONFIG]` — API config built

## Test Commands

```bash
# Run all external model API tests
cd docling-serve
python -m pytest tests/test_external_model_api.py -v

# Run with LDD log output
python -m pytest tests/test_external_model_api.py -v -s

# Run single test class
python -m pytest tests/test_external_model_api.py::TestExternalModelRegistry -v

# Run integration test only
python -m pytest tests/test_external_model_api.py::TestIntegrationExternalModelFlow -v
```

## Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DOCLING_SERVE_EXTERNAL_MODEL_ENABLED` | bool | False | Master switch for external models |
| `DOCLING_SERVE_EXTERNAL_MODEL_BASE_URL` | str | "" | Base URL (e.g., http://localhost:11434/v1) |
| `DOCLING_SERVE_EXTERNAL_MODEL_API_KEY` | str | "" | API key for external service |
| `DOCLING_SERVE_EXTERNAL_MODEL_TIMEOUT` | float | 60.0 | Request timeout in seconds |
| `DOCLING_SERVE_EXTERNAL_MODEL_DEFAULT_MODEL` | str | "" | Default model name |

## Acceptance Criteria Verification

- [x] **Criterion 1:** Settings contains `external_model_*` fields
- [x] **Criterion 2:** ServicePolicy includes `external_models_enabled`
- [x] **Criterion 3:** `convert_options_extender.py` with ExternalModelConfig and ExternalModelRegistry
- [x] **Criterion 4:** Backward compatibility with existing `picture_description_api` format
- [x] **Criterion 7:** Unit tests for settings parsing, policy validation, and registry
- [ ] **Criterion 8:** Integration test with Ollama/vLLM (requires running API server)

## Notes for QA

1. Tests verify configuration parsing and registry operations without requiring an actual external API server.
2. Integration test (Criterion 8) requires a running Ollama or vLLM server to verify end-to-end conversion.
3. LDD logs are captured at IMP:5+ level for traceability.