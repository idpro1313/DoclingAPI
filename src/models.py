"""Request/Response models for docling-external-api FastAPI server."""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

_log = logging.getLogger(__name__)


# region MODULE_CONTRACT [DOMAIN(7): API Models; CONCEPT(6): Pydantic, FastAPI; TECH(8): pydantic]
## @modulecontract
## @purpose Pydantic модели для HTTP запросов/ответов API.
## @scope Конвертация документов, проксирование в docling-serve.
## @input Request/Response JSON модели.
## @output Валидированные модели для FastAPI endpoints.
## @invariants
## - Все модели наследуются от BaseModel
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
## @modulemap
## CLASS 8[Source conversion request] => ConvertSourceRequest
## CLASS 6[Conversion response] => ConvertSourceResponse
## CLASS 5[Health response] => HealthResponse
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: API models, Pydantic, FastAPI, request, response, convert
# STRUCTURE: ▶ Init ┌Request JSON┐ → ○ Validation → ⊕ Response Model → ⎋ return


# region CLASS_ConvertSourceRequest [DOMAIN(7): API; CONCEPT(7): Conversion; TECH(8): pydantic]
## @purpose Request model для POST /v1/convert/source endpoint.
## @io dict -> ConvertSourceRequest
## @complexity 5
class SourceItem(BaseModel):
    """Single source item for conversion."""

    kind: str = Field(..., description="Source type: 'file', 'http', 'url'")
    uri: Optional[str] = Field(None, description="File path or URL")
    data: Optional[str] = Field(None, description="Base64 encoded data")
    mime: Optional[str] = Field(None, description="MIME type")

    model_config = {"extra": "allow"}


class ConvertSourceRequest(BaseModel):
    """Request body for document conversion endpoint."""

    sources: list[SourceItem] = Field(..., description="List of sources to convert")
    max_num_images: int = Field(default=10, description="Maximum number of images per page")
    timeout: Optional[float] = Field(default=120.0, description="Request timeout in seconds")

    model_config = {"extra": "allow"}
# endregion CLASS_ConvertSourceRequest


# region CLASS_ConvertSourceResponse [DOMAIN(7): API; CONCEPT(7): Conversion; TECH(8): pydantic]
## @purpose Response model для document conversion.
## @io dict -> ConvertSourceResponse
## @complexity 5
class ConvertSourceResponse(BaseModel):
    """Response from document conversion."""

    status: str = Field(..., description="Conversion status")
    document: Optional[dict[str, Any]] = Field(None, description="Converted document")
    task_id: Optional[str] = Field(None, description="Task ID for async operations")
    error: Optional[str] = Field(None, description="Error message if failed")

    model_config = {"extra": "allow"}
# endregion CLASS_ConvertSourceResponse


# region CLASS_HealthResponse [DOMAIN(5): API; CONCEPT(5): Health; TECH(7): pydantic]
## @purpose Response model для health check endpoint.
## @io dict -> HealthResponse
## @complexity 3
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(default="0.3.0", description="Service version")
    docling_serve_url: str = Field(..., description="Configured docling-serve URL")
    vlm_enabled: bool = Field(default=False, description="Whether VLM is enabled")
# endregion CLASS_HealthResponse