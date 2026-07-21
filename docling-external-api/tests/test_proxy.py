# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): Proxy, HTTP; TECH(8): pytest, httpx]
## @modulecontract
## @purpose Tests for proxy module (HTTP proxy to docling-serve).
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, proxy, HTTP, httpx, docling-serve

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.proxy import convert_document, health_check


# region FUNC_test_convert_document_success [DOMAIN(5): Testing; CONCEPT(6): Proxy; TECH(8): pytest]
## @purpose Test successful document conversion via proxy.
## @io None -> None
## @complexity 6
@pytest.mark.asyncio
async def test_convert_document_success():
    """Test convert_document calls docling-serve and returns result."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success", "pages": [{"num": 1}]}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.proxy.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.docling_serve_url = "http://localhost:5001"
        mock_get_config.return_value = mock_config

        with patch("src.proxy.httpx.AsyncClient", return_value=mock_client):
            result = await convert_document({"sources": [{"kind": "url", "uri": "test.pdf"}]})

    assert result["status"] == "success"
    assert "pages" in result

    print("[IMP:6][test_convert_document_success][PASS] Proxy success OK")
# endregion FUNC_test_convert_document_success


# region FUNC_test_convert_document_with_timeout [DOMAIN(5): Testing; CONCEPT(6): Proxy; TECH(8): pytest]
## @purpose Test convert_document uses timeout from request.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_convert_document_with_timeout():
    """Test convert_document passes timeout to httpx client."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "success"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.proxy.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.docling_serve_url = "http://localhost:5001"
        mock_get_config.return_value = mock_config

        with patch("src.proxy.httpx.AsyncClient", return_value=mock_client):
            await convert_document({"sources": [], "timeout": 60.0, "max_num_images": 5})

            mock_client.post.assert_called_once()
            call_kwargs = mock_client.post.call_args
            assert call_kwargs.kwargs.get("timeout") == 60.0

    print("[IMP:5][test_convert_document_with_timeout][PASS] Timeout passed OK")
# endregion FUNC_test_convert_document_with_timeout


# region FUNC_test_health_check_healthy [DOMAIN(5): Testing; CONCEPT(6): Health; TECH(8): pytest]
## @purpose Test health_check returns True when docling-serve is healthy.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_health_check_healthy():
    """Test health_check returns True for healthy docling-serve."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.proxy.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.docling_serve_url = "http://localhost:5001"
        mock_get_config.return_value = mock_config

        with patch("src.proxy.httpx.AsyncClient", return_value=mock_client):
            result = await health_check()

    assert result is True

    print("[IMP:5][test_health_check_healthy][PASS] Health check healthy OK")
# endregion FUNC_test_health_check_healthy


# region FUNC_test_health_check_unhealthy [DOMAIN(5): Testing; CONCEPT(6): Health; TECH(8): pytest]
## @purpose Test health_check returns False when docling-serve is down.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_health_check_unhealthy():
    """Test health_check returns False when docling-serve is unreachable."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Connection refused")
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.proxy.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.docling_serve_url = "http://localhost:5001"
        mock_get_config.return_value = mock_config

        with patch("src.proxy.httpx.AsyncClient", return_value=mock_client):
            result = await health_check()

    assert result is False

    print("[IMP:5][test_health_check_unhealthy][PASS] Health check unhealthy OK")
# endregion FUNC_test_health_check_unhealthy


# region FUNC_test_health_check_http_error [DOMAIN(5): Testing; CONCEPT(6): Health; TECH(8): pytest]
## @purpose Test health_check returns False on HTTP error.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_health_check_http_error():
    """Test health_check returns False on HTTP 500 error."""
    import httpx

    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.proxy.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.docling_serve_url = "http://localhost:5001"
        mock_get_config.return_value = mock_config

        with patch("src.proxy.httpx.AsyncClient", return_value=mock_client):
            result = await health_check()

    assert result is False

    print("[IMP:5][test_health_check_http_error][PASS] Health check HTTP error OK")
# endregion FUNC_test_health_check_http_error