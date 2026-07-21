# region MODULE_CONTRACT [DOMAIN(5): Testing; CONCEPT(6): VLM, Vision; TECH(8): pytest]
## @modulecontract
## @purpose Tests for VLM handler module (pass-through mode - VLM now in docling-serve).
## @changes
## LAST_CHANGE: v0.4.0 - VLM integration moved to docling-serve via ENV config
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Testing, VLM, vision, language model, image processing, pass-through

import pytest
from unittest.mock import patch, MagicMock

from src.vlm_handler import (
    extract_pages,
    process_with_vlm,
)


# region FUNC_test_extract_pages_empty [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages returns empty list (deprecated).
## @io None -> None
## @complexity 3
def test_extract_pages_empty():
    """Test extract_pages returns empty list (VLM now in docling-serve)."""
    result = extract_pages(None)
    assert result == []

    result = extract_pages({})
    assert result == []

    print("[IMP:3][test_extract_pages_empty][PASS] Deprecated returns empty OK")
# endregion FUNC_test_extract_pages_empty


# region FUNC_test_extract_pages_from_pages [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages returns empty (deprecated function).
## @io None -> None
## @complexity 3
def test_extract_pages_from_pages():
    """Test extract_pages returns empty (VLM now in docling-serve)."""
    doc = {
        "pages": [
            {"num": 1, "text": "Page 1"},
            {"num": 2, "text": "Page 2"},
        ]
    }

    result = extract_pages(doc)

    assert result == []

    print("[IMP:3][test_extract_pages_from_pages][PASS] Deprecated returns empty OK")
# endregion FUNC_test_extract_pages_from_pages


# region FUNC_test_extract_pages_from_documents [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test extract_pages returns empty (deprecated function).
## @io None -> None
## @complexity 3
def test_extract_pages_from_documents():
    """Test extract_pages returns empty (VLM now in docling-serve)."""
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

    assert result == []

    print("[IMP:3][test_extract_pages_from_documents][PASS] Deprecated returns empty OK")
# endregion FUNC_test_extract_pages_from_documents


# region FUNC_test_process_with_vlm_passthrough [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test process_with_vlm returns original doc (pass-through mode).
## @io None -> None
## @complexity 4
@pytest.mark.asyncio
async def test_process_with_vlm_passthrough():
    """Test process_with_vlm returns original doc (VLM handled by docling-serve)."""
    doc = {"pages": [{"num": 1, "vlm_result": "already_applied"}]}

    result = await process_with_vlm(doc)

    assert result == doc
    assert result.get("pages")[0].get("vlm_result") == "already_applied"

    print("[IMP:4][test_process_with_vlm_passthrough][PASS] Pass-through returns original OK")
# endregion FUNC_test_process_with_vlm_passthrough


# region FUNC_test_process_with_vlm_preserves_content [DOMAIN(5): Testing; CONCEPT(6): VLM; TECH(8): pytest]
## @purpose Test process_with_vlm preserves all document content.
## @io None -> None
## @complexity 4
@pytest.mark.asyncio
async def test_process_with_vlm_preserves_content():
    """Test process_with_vlm preserves all document content."""
    doc = {
        "documents": [
            {
                "pages": [
                    {"num": 1, "text": "Page 1", "images": []},
                    {"num": 2, "text": "Page 2", "images": []},
                ]
            }
        ],
        "metadata": {"source": "test.pdf", "vlm_model": "minimax-m2.7"}
    }

    result = await process_with_vlm(doc)

    assert result == doc
    assert result["metadata"]["vlm_model"] == "minimax-m2.7"

    print("[IMP:4][test_process_with_vlm_preserves_content][PASS] Content preserved OK")
# endregion FUNC_test_process_with_vlm_preserves_content