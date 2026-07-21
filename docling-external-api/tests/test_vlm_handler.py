# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): VLM, Vision; TECH(8): pytest]
## @modulecontract
## @purpose Tests for VLM handler module (post-processing VLM mode).
## @changes
## LAST_CHANGE: v0.3.1 - Post-processing VLM mode
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, VLM, vision, language model, image processing

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.vlm_handler import (
    extract_pages,
    process_with_vlm,
    call_vlm,
)


# region FUNC_test_extract_pages_empty [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages with empty document.
## @io None -> None
## @complexity 4
def test_extract_pages_empty():
    """Test extract_pages returns empty list for None."""
    result = extract_pages(None)
    assert result == []

    result = extract_pages({})
    assert result == []

    print("[IMP:4][test_extract_pages_empty][PASS] Empty doc extraction OK")
# endregion FUNC_test_extract_pages_empty


# region FUNC_test_extract_pages_from_pages [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages from document with 'pages' key.
## @io None -> None
## @complexity 4
def test_extract_pages_from_pages():
    """Test extract_pages extracts from 'pages' key."""
    doc = {
        "pages": [
            {"num": 1, "text": "Page 1"},
            {"num": 2, "text": "Page 2"},
        ]
    }

    result = extract_pages(doc)

    assert len(result) == 2
    assert result[0]["num"] == 1
    assert result[1]["num"] == 2

    print("[IMP:4][test_extract_pages_from_pages][PASS] Pages extraction OK")
# endregion FUNC_test_extract_pages_from_pages


# region FUNC_test_extract_pages_from_documents [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages from document with 'documents' key.
## @io None -> None
## @complexity 5
def test_extract_pages_from_documents():
    """Test extract_pages extracts from 'documents[0].pages' key."""
    doc = {
        "documents": [
            {
                "pages": [
                    {"num": 1, "text": "Page 1"},
                ]
            }
        ]
    }

    result = extract_pages(doc)

    assert len(result) == 1
    assert result[0]["num"] == 1

    print("[IMP:5][test_extract_pages_from_documents][PASS] Documents extraction OK")
# endregion FUNC_test_extract_pages_from_documents


# region FUNC_test_process_with_vlm_disabled [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test process_with_vlm returns original when VLM disabled.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_process_with_vlm_disabled():
    """Test process_with_vlm returns original doc when VLM is disabled."""
    doc = {"pages": [{"num": 1}]}

    with patch("src.vlm_handler.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.vlm_enabled = False
        mock_get_config.return_value = mock_config

        result = await process_with_vlm(doc)

    assert result == doc

    print("[IMP:5][test_process_with_vlm_disabled][PASS] Disabled VLM returns original OK")
# endregion FUNC_test_process_with_vlm_disabled


# region FUNC_test_process_with_vlm_no_pages [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test process_with_vlm returns original when no pages.
## @io None -> None
## @complexity 5
@pytest.mark.asyncio
async def test_process_with_vlm_no_pages():
    """Test process_with_vlm returns original doc when no pages found."""
    doc = {"other": "data"}

    with patch("src.vlm_handler.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.vlm_enabled = True
        mock_config.vlm_model = "test-model"
        mock_get_config.return_value = mock_config

        result = await process_with_vlm(doc)

    assert result == doc

    print("[IMP:5][test_process_with_vlm_no_pages][PASS] No pages returns original OK")
# endregion FUNC_test_process_with_vlm_no_pages


# region FUNC_test_call_vlm_success [DOMAIN(5): Testing; CONCEPT(6): VLM API; TECH(8): pytest]
## @purpose Test call_vlm makes correct API call.
## @io None -> None
## @complexity 7
@pytest.mark.asyncio
async def test_call_vlm_success():
    """Test call_vlm constructs correct payload and calls VLM API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}],
        "usage": {"total_tokens": 100},
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("src.vlm_handler.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.vlm_enabled = True
        mock_config.vlm_base_url = "https://api.test.com/v1"
        mock_config.vlm_api_key = "sk-test"
        mock_config.vlm_model = "test-model"
        mock_config.vlm_timeout = 120.0
        mock_get_config.return_value = mock_config

        with patch("src.vlm_handler.httpx.AsyncClient", return_value=mock_client):
            result = await call_vlm({"base64": "SGVsbG8="}, page_num=0, img_idx=0)

    mock_client.post.assert_called_once()
    call_kwargs = mock_client.post.call_args
    assert call_kwargs.kwargs.get("url") == "https://api.test.com/v1/chat/completions"

    print("[IMP:7][test_call_vlm_success][PASS] VLM API call OK")
# endregion FUNC_test_call_vlm_success


# region FUNC_test_call_vlm_disabled [DOMAIN(5): Testing; CONCEPT(6): VLM API; TECH(8): pytest]
## @purpose Test call_vlm returns error when VLM disabled.
## @io None -> None
## @complexity 4
@pytest.mark.asyncio
async def test_call_vlm_disabled():
    """Test call_vlm returns error dict when VLM is disabled."""
    with patch("src.vlm_handler.get_config") as mock_get_config:
        mock_config = MagicMock()
        mock_config.vlm_enabled = False
        mock_get_config.return_value = mock_config

        result = await call_vlm({"base64": "SGVsbG8="}, page_num=0, img_idx=0)

    assert "error" in result
    assert result["error"] == "VLM not enabled"

    print("[IMP:4][test_call_vlm_disabled][PASS] Disabled VLM returns error OK")
# endregion FUNC_test_call_vlm_disabled