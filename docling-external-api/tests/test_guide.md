# Test Guide: docling-external-api Plugin

## Overview

Plugin for connecting external OpenAI-compatible APIs to docling-serve for VLM, OCR, Table Structure, Picture Description, and Layout models.

## Test Files

| File | Description | Coverage |
|------|-------------|----------|
| `test_config.py` | ExternalApiConfig class tests | 8 tests |
| `test_integration.py` | Integration and plugin tests | 7 tests |

## Running Tests

```bash
cd docling-external-api
python -m pytest tests/ -v -s
```

## Test Data Requirements

No external test data required. Tests use:
- Environment variable mocking (`monkeypatch`)
- In-memory configuration objects

## Expected Log Markers (LDD)

### IMP:7-10 Markers to Verify

**config.py tests:**
```
[IMP:5] [ExternalApiConfig][VALIDATE] Engine enabled but no base_url configured
[IMP:7] [ExternalApiConfig][GET_VLM_PRESET] Creating VLM preset for model=
[IMP:7] [ExternalApiConfig][GET_ALL_PRESETS] Generated presets for engines:
```

**integration.py tests:**
```
[IMP:4] [test_setup_external_api_no_config][PASS] Empty config returns empty dict OK
[IMP:6] [test_setup_external_api_vlm_only][PASS] VLM only setup OK
[IMP:6] [test_setup_external_api_multiple_engines][PASS] Multiple engines setup OK
[IMP:5] [test_setup_external_api_auto_load][PASS] Auto-load from env OK
[IMP:4] [test_register_plugin][PASS] Plugin registration OK
[IMP:5] [test_preset_contains_required_fields][PASS] Required fields OK
```

## Verification Queries

### Check config loads from env
```python
import os
os.environ["EXTERNAL_API_VLM_ENABLED"] = "1"
os.environ["EXTERNAL_API_VLM_BASE_URL"] = "https://api.openai.com/v1"
config = ExternalApiConfig()
assert config.vlm_enabled == True
```

### Check preset structure
```python
config = ExternalApiConfig(vlm_enabled=True, vlm_base_url="https://api.openai.com/v1", vlm_api_key="sk-test")
result = setup_external_api(config)
assert "custom_vlm_presets" in result
assert "external_api_vlm" in result["custom_vlm_presets"]
preset = result["custom_vlm_presets"]["external_api_vlm"]
assert preset["url"] == "https://api.openai.com/v1/chat/completions"
```

## Acceptance Criteria

- [ ] All 15 tests pass
- [ ] LDD logs with IMP:7-10 are visible in test output
- [ ] Plugin entry point `docling_external_api.plugin:plugin` is registered in pyproject.toml
- [ ] No hardcoded paths in tests
- [ ] Semantic markup (# region / # endregion) present in all source files