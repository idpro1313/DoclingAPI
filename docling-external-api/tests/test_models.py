# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): Models, API; TECH(7): pytest]
## @modulecontract
## @purpose Tests for Pydantic models (Request/Response).
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, models, pydantic, request, response, convert

import pytest

from src.models import (
    ConvertSourceRequest,
    ConvertSourceResponse,
    HealthResponse,
    SourceItem,
)


# region FUNC_test_source_item [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test SourceItem model creation.
## @io None -> None
## @complexity 3
def test_source_item():
    """Test SourceItem creation with required fields."""
    item = SourceItem(kind="url", uri="https://example.com/doc.pdf")

    assert item.kind == "url"
    assert item.uri == "https://example.com/doc.pdf"
    assert item.data is None
    assert item.mime is None

    print("[IMP:4][test_source_item][PASS] SourceItem creation OK")
# endregion FUNC_test_source_item


# region FUNC_test_source_item_with_data [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test SourceItem with base64 data.
## @io None -> None
## @complexity 4
def test_source_item_with_data():
    """Test SourceItem with base64 encoded data."""
    item = SourceItem(
        kind="file",
        data="SGVsbG8gV29ybGQ=",
        mime="application/pdf"
    )

    assert item.kind == "file"
    assert item.data == "SGVsbG8gV29ybGQ="
    assert item.mime == "application/pdf"

    print("[IMP:4][test_source_item_with_data][PASS] SourceItem with data OK")
# endregion FUNC_test_source_item_with_data


# region FUNC_test_convert_source_request [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test ConvertSourceRequest model.
## @io None -> None
## @complexity 4
def test_convert_source_request():
    """Test ConvertSourceRequest with sources."""
    request = ConvertSourceRequest(
        sources=[
            SourceItem(kind="url", uri="https://example.com/doc1.pdf"),
            SourceItem(kind="url", uri="https://example.com/doc2.pdf"),
        ],
        max_num_images=20,
        timeout=300.0,
    )

    assert len(request.sources) == 2
    assert request.max_num_images == 20
    assert request.timeout == 300.0

    print("[IMP:5][test_convert_source_request][PASS] ConvertSourceRequest OK")
# endregion FUNC_test_convert_source_request


# region FUNC_test_convert_source_request_default_timeout [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test ConvertSourceRequest default values.
## @io None -> None
## @complexity 3
def test_convert_source_request_default_timeout():
    """Test ConvertSourceRequest has sensible defaults."""
    request = ConvertSourceRequest(
        sources=[SourceItem(kind="url", uri="https://example.com/doc.pdf")]
    )

    assert request.max_num_images == 10
    assert request.timeout == 120.0

    print("[IMP:4][test_convert_source_request_default_timeout][PASS] Default timeout OK")
# endregion FUNC_test_convert_source_request_default_timeout


# region FUNC_test_convert_source_response_success [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test ConvertSourceResponse success case.
## @io None -> None
## @complexity 3
def test_convert_source_response_success():
    """Test ConvertSourceResponse with success status."""
    response = ConvertSourceResponse(
        status="success",
        document={"pages": [{"num": 1}]},
    )

    assert response.status == "success"
    assert response.document is not None
    assert response.error is None

    print("[IMP:4][test_convert_source_response_success][PASS] Success response OK")
# endregion FUNC_test_convert_source_response_success


# region FUNC_test_convert_source_response_error [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test ConvertSourceResponse error case.
## @io None -> None
## @complexity 3
def test_convert_source_response_error():
    """Test ConvertSourceResponse with error status."""
    response = ConvertSourceResponse(
        status="error",
        error="Connection timeout",
    )

    assert response.status == "error"
    assert response.error == "Connection timeout"
    assert response.document is None

    print("[IMP:4][test_convert_source_response_error][PASS] Error response OK")
# endregion FUNC_test_convert_source_response_error


# region FUNC_test_health_response [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test HealthResponse model.
## @io None -> None
## @complexity 3
def test_health_response():
    """Test HealthResponse with all fields."""
    response = HealthResponse(
        status="healthy",
        version="0.3.0",
        docling_serve_url="http://localhost:5001",
        vlm_enabled=True,
    )

    assert response.status == "healthy"
    assert response.version == "0.3.0"
    assert response.vlm_enabled is True

    print("[IMP:4][test_health_response][PASS] HealthResponse OK")
# endregion FUNC_test_health_response


# region FUNC_test_health_response_degraded [DOMAIN(5): Testing; CONCEPT(6): Models; TECH(7): pytest]
## @purpose Test HealthResponse degraded status.
## @io None -> None
## @complexity 3
def test_health_response_degraded():
    """Test HealthResponse with degraded status."""
    response = HealthResponse(
        status="degraded",
        version="0.3.0",
        docling_serve_url="http://localhost:5001",
        vlm_enabled=False,
    )

    assert response.status == "degraded"
    assert response.vlm_enabled is False

    print("[IMP:4][test_health_response_degraded][PASS] Degraded status OK")
# endregion FUNC_test_health_response_degraded