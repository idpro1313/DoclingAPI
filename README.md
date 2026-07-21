# docling-external-api

External API Plugin for docling-serve with OpenAI-compatible model support.

## Overview

This plugin allows connecting external OpenAI-compatible APIs (OpenAI, Azure OpenAI, vLLM, Ollama, LM Studio, etc.) to docling-serve for:

- **VLM** (Vision-Language Models) - Document page analysis
- **OCR** (Optical Character Recognition) - Text recognition
- **Table Structure** - Table detection and structure recognition
- **Picture Description** - Image description and captioning
- **Layout** - Document layout analysis

## Installation

```bash
pip install docling-external-api
```

## Configuration

### Environment Variables

```bash
# VLM Configuration
export EXTERNAL_API_VLM_ENABLED=1
export EXTERNAL_API_VLM_BASE_URL=https://api.openai.com/v1
export EXTERNAL_API_VLM_API_KEY=sk-your-api-key
export EXTERNAL_API_VLM_MODEL=gpt-4o

# OCR Configuration (optional)
export EXTERNAL_API_OCR_ENABLED=1
export EXTERNAL_API_OCR_BASE_URL=https://api.openai.com/v1
export EXTERNAL_API_OCR_API_KEY=sk-your-api-key

# Table Structure Configuration (optional)
export EXTERNAL_API_TABLE_ENABLED=1
export EXTERNAL_API_TABLE_BASE_URL=https://api.openai.com/v1
export EXTERNAL_API_TABLE_API_KEY=sk-your-api-key
```

### Python API

```python
from docling_external_api import setup_external_api, ExternalApiConfig

# Option 1: From environment
preset_config = setup_external_api()

# Option 2: Explicit configuration
config = ExternalApiConfig(
    vlm_enabled=True,
    vlm_base_url="https://api.openai.com/v1",
    vlm_api_key="sk-...",
    vlm_model="gpt-4o"
)
preset_config = setup_external_api(config)

# Use preset_config in DoclingConverterManagerConfig
```

## Usage with docling-serve

```python
from docling_serve.settings import DoclingServeSettings
from docling_external_api import setup_external_api

# Load external API configuration
preset_config = setup_external_api()

# Apply to docling-serve settings
if preset_config:
    for key, value in preset_config.items():
        setattr(DoclingServeSettings(), key, value)
```

## License

MIT