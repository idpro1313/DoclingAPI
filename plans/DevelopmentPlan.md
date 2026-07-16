# Development Plan: External API Models for Docling

**PURPOSE:** Enable VLM and LLM models via OpenAI-compatible API endpoints (vLLM, Ollama, etc.) for document processing pipeline.

---

### 1. Draft Code Graph

```xml
<DraftCodeGraph>
  <settings_py FILE="docling-serve/docling_serve/settings.py" TYPE="CONFIG">
    <annotation>Configuration for external model API endpoints and credentials.</annotation>
    <settings_py_DoclingServeSettings_CLASS NAME="DoclingServeSettings" TYPE="IS_CLASS_OF_MODULE">
      <annotation>Central settings class containing all configuration parameters.</annotation>
      <settings_py_DoclingServeSettings_external_model_base_url_FIELD NAME="external_model_base_url" TYPE="IS_FIELD_OF_CLASS">
        <annotation>Base URL for OpenAI-compatible API endpoint.</annotation>
      </settings_py_DoclingServeSettings_external_model_base_url_FIELD>
      <settings_py_DoclingServeSettings_external_model_api_key_FIELD NAME="external_model_api_key" TYPE="IS_FIELD_OF_CLASS">
        <annotation>API key for external model service.</annotation>
      </settings_py_DoclingServeSettings_external_model_api_key_FIELD>
      <settings_py_DoclingServeSettings_external_model_timeout_FIELD NAME="external_model_timeout" TYPE="IS_FIELD_OF_CLASS">
        <annotation>Timeout for external model API calls.</annotation>
      </settings_py_DoclingServeSettings_external_model_timeout_FIELD>
      <settings_py_DoclingServeSettings_external_model_default_model_FIELD NAME="external_model_default_model" TYPE="IS_FIELD_OF_CLASS">
        <annotation>Default model name when not specified per-request.</annotation>
      </settings_py_DoclingServeSettings_external_model_default_model_FIELD>
    </settings_py_DoclingServeSettings_CLASS>
  </settings_py>

  <policy_py FILE="docling-serve/docling_serve/policy.py" TYPE="POLICY">
    <annotation>Service policy and validation for external model configuration.</annotation>
    <policy_py_ServicePolicy_CLASS NAME="ServicePolicy" TYPE="IS_CLASS_OF_MODULE">
      <annotation>Policy class holding allowed model configurations.</annotation>
      <policy_py_ServicePolicy_external_models_enabled_FIELD NAME="external_models_enabled" TYPE="IS_FIELD_OF_CLASS">
        <annotation>Whether external API models are allowed.</annotation>
      </policy_py_ServicePolicy_external_models_enabled_FIELD>
    </policy_py_ServicePolicy_CLASS>
    <policy_py_validate_convert_options_FUNCTION NAME="validate_convert_options" TYPE="IS_FUNCTION_IN_MODULE">
      <annotation>Validates convert options including model configuration.</annotation>
    </policy_py_validate_convert_options_FUNCTION>
  </policy_py>

  <convert_options_extender_py FILE="docling-serve/docling_serve/convert_options_extender.py" TYPE="PLUGIN">
    <annotation>Plugin system for extending ConvertDocumentsOptions with external model configs.</annotation>
    <convert_options_extender_py_ExternalModelConfig_CLASS NAME="ExternalModelConfig" TYPE="IS_CLASS_IN_MODULE">
      <annotation>Configuration for a single external model endpoint.</annotation>
    </convert_options_extender_py_ExternalModelConfig_CLASS>
    <convert_options_extender_py_ExternalModelRegistry_CLASS NAME="ExternalModelRegistry" TYPE="IS_CLASS_IN_MODULE">
      <annotation>Registry for managing multiple external model configurations.</annotation>
      <convert_options_extender_py_ExternalModelRegistry_register_METHOD NAME="register" TYPE="IS_METHOD_OF_CLASS">
        <annotation>Register a new external model configuration.</annotation>
      </convert_options_extender_py_ExternalModelRegistry_register_METHOD>
      <convert_options_extender_py_ExternalModelRegistry_get_CONFIG_METHOD NAME="get_config" TYPE="IS_METHOD_OF_CLASS">
        <annotation>Retrieve configuration for a named model.</annotation>
      </convert_options_extender_py_ExternalModelRegistry_get_config_METHOD>
    </convert_options_extender_py_ExternalModelRegistry_CLASS>
  </convert_options_extender_py>

  <app_py FILE="docling-serve/docling_serve/app.py" TYPE="API">
    <annotation>Main FastAPI application with endpoints for model configuration.</annotation>
    <app_py_create_app_FUNCTION NAME="create_app" TYPE="IS_FUNCTION_IN_MODULE">
      <annotation>Application factory creating FastAPI app with model endpoints.</annotation>
    </app_py_create_app_FUNCTION>
    <app_py_management_endpoints_REGION NAME="management_endpoints" TYPE="REGION_IN_MODULE">
      <annotation>Management API endpoints for model configuration.</annotation>
    </app_py_management_endpoints_REGION>
  </app_py>
</DraftCodeGraph>
```

---

### 2. Step-by-step Data Flow

**Hypothesis A: Centralized Config (Recommended)**
```
▶ Request → ○ Load external_model_config from settings
→ ◇ Validate model name against allowed list
→ ◇ Build API headers (api_key, base_url, timeout)
→ ◇ Merge with request-specific params (model override)
→ ⊕ Pass to docling pipeline
→ ⟦Docling pipeline makes API calls⟧
→ ⎋ Return processed document
```

**Hypothesis B: Per-Request Config (Alternative)**
```
▶ Request with vlm_api_config → ○ Validate inline config
→ ◇ Check allow_custom_vlm_config flag
→ ◇ Extract base_url, model, api_key from request
→ ⊕ Build API client dynamically
→ ⟦Docling pipeline uses dynamic client⟧
→ ⎋ Return processed document
```

**Selected: Hypothesis A** — Centralized configuration is more secure, maintainable, and aligns with existing settings pattern.

**Data Flow (Selected):**
1. **Step 1:** Load `external_model_base_url`, `external_model_api_key`, `external_model_timeout` from settings at startup.
2. **Step 2:** Validate request's `vlm_pipeline_api` or `picture_description_api` against allowed models list.
3. **Step 3:** If request omits explicit API config, apply server defaults from settings.
4. **Step 4:** Build HTTP client with proper headers, base URL, and timeout.
5. **Step 5:** Pass configured API params to docling pipeline components (VLM, Picture Description, Code/Formula).
6. **Step 6:** Handle API errors with proper HTTP status codes and logging.

---

### 3. Acceptance Criteria

- [ ] **Criterion 1:** Settings file (`settings.py`) contains new fields: `external_model_base_url`, `external_model_api_key`, `external_model_timeout`, `external_model_default_model`, `external_model_enabled`.
- [ ] **Criterion 2:** ServicePolicy includes `external_models_enabled` flag and policy is checked before allowing external API calls.
- [ ] **Criterion 3:** New module `convert_options_extender.py` provides `ExternalModelConfig` dataclass and `ExternalModelRegistry` for named model configurations.
- [ ] **Criterion 4:** Existing `picture_description_api` parameter works with new external model config system.
- [ ] **Criterion 5:** VLM pipeline (`vlm_pipeline_api`) can be configured via external API (if supported by docling).
- [ ] **Criterion 6:** LLM post-processing (structure extraction, formatting) can use external API if docling supports it.
- [ ] **Criterion 7:** Unit tests cover settings parsing, policy validation, and model registry operations.
- [ ] **Criterion 8:** Integration test demonstrates end-to-end conversion with Ollama/vLLM external API.

---

### 4. Implementation Notes

#### Phase 1: Configuration Layer
- Add settings in `DoclingServeSettings`:
  - `external_model_enabled: bool = False` — master switch
  - `external_model_base_url: str = ""` — e.g., `http://localhost:11434/v1`
  - `external_model_api_key: str = ""` — optional for local services
  - `external_model_timeout: float = 60.0` — default timeout in seconds
  - `external_model_default_model: str = ""` — default model name

#### Phase 2: Policy Layer
- Extend `ServicePolicy` with `external_models_enabled: bool`
- Add validation in `validate_convert_options()` for model configuration

#### Phase 3: Model Registry
- Create `convert_options_extender.py` with:
  - `ExternalModelConfig` — dataclass for single model config
  - `ExternalModelRegistry` — singleton for managing named configurations

#### Phase 4: Integration
- Ensure backward compatibility with existing `picture_description_api` JSON format
- Support both server-default and per-request API configurations