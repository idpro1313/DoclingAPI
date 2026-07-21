"""docling-external-api - Standalone service for external API integration with docling-serve."""

from docling_external_api.config import ExternalApiConfig, get_config, load_config
from docling_external_api.models import (
    ConvertSourceRequest,
    ConvertSourceResponse,
    HealthResponse,
    SourceItem,
)

__version__ = "0.3.0"

__all__ = [
    "ExternalApiConfig",
    "get_config",
    "load_config",
    "ConvertSourceRequest",
    "ConvertSourceResponse",
    "HealthResponse",
    "SourceItem",
]