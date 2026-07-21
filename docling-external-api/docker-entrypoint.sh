#!/bin/bash
# Entrypoint for docling-external-api plugin
# Configures external API settings before starting docling-serve

set -e

echo "[ENTRYPOINT] Starting docling-external-api plugin..."
echo "[ENTRYPOINT] VLM Base URL: ${EXTERNAL_API_VLM_BASE_URL:-not set}"
echo "[ENTRYPOINT] VLM Model: ${EXTERNAL_API_VLM_MODEL:-not set}"
echo "[ENTRYPOINT] VLM Enabled: ${EXTERNAL_API_VLM_ENABLED:-false}"

# If external API is enabled, print configuration
if [ "${EXTERNAL_API_VLM_ENABLED}" = "1" ]; then
    echo "[ENTRYPOINT] External VLM API is ENABLED"

    # Create a Python configuration script
    cat > /tmp/configure_external_api.py << 'PYEOF'
import os
import sys

# Add plugin path
sys.path.insert(0, '/opt/app-root/src')

try:
    from docling_external_api import setup_external_api, ExternalApiConfig
    from docling_serve.settings import DoclingServeSettings

    # Load config from environment
    config = ExternalApiConfig()

    if config.is_any_enabled:
        print("[ENTRYPOINT] External API configuration loaded successfully")
        print(f"[ENTRYPOINT] Enabled engines: {config.enabled_engines}")

        # Get preset configuration
        preset_config = setup_external_api(config)

        if preset_config:
            print("[ENTRYPOINT] Preset configuration generated:")
            for key, value in preset_config.items():
                if 'api_key' not in str(value).lower():
                    print(f"  - {key}: {value}")

            # Apply to settings (this modifies docling_serve_settings)
            for key, value in preset_config.items():
                setattr(DoclingServeSettings(), key, value)

            print("[ENTRYPOINT] External API configuration applied to docling-serve")
        else:
            print("[ENTRYPOINT] No preset configuration generated")
    else:
        print("[ENTRYPOINT] No external APIs enabled in config")

except Exception as e:
    print(f"[ENTRYPOINT] WARNING: Could not configure external API: {e}")
    import traceback
    traceback.print_exc()
    # Continue anyway - original models will be used

PYEOF

    python /tmp/configure_external_api.py
fi

echo "[ENTRYPOINT] Starting docling-serve..."
exec "$@"