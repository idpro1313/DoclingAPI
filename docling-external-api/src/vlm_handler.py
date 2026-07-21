"""VLM (Vision Language Model) handler for enriching document results."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from src.config import get_config

_log = logging.getLogger(__name__)


# region MODULE_CONTRACT [DOMAIN(6): VLM; CONCEPT(7): Vision, Language Model; TECH(8): httpx, OpenAI]
## @modulecontract
## @purpose VLM теперь интегрирован в docling-serve через ENV variables. Этот модуль - pass-through fallback.
## @scope Документы передаются как есть. VLM вызовы выполняются docling-serve автоматически.
## @input Document result от docling-serve
## @output Оригинальный document без изменений
## @links [USES_API(4): httpx]
## @invariants
## - process_with_vlm всегда возвращает документ без изменений
## @changes
## LAST_CHANGE: v0.4.0 - VLM integration moved to docling-serve ENV config
## @modulemap
## FUNC 6[Pass-through] => process_with_vlm
## FUNC 5[Pass-through] => extract_pages
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: VLM, vision, language model, image processing, external API, minimax
# STRUCTURE: ▶ DocResult → ○ Extract Pages → ⚡ Call VLM API → ⊕ Merge Results → ⎋ EnrichedDoc


# region FUNC_process_with_vlm [DOMAIN(5): VLM; CONCEPT(5): Pass-through; TECH(5): httpx]
## @purpose Pass-through для обратной совместимости. VLM теперь встроен в docling-serve.
## @io dict -> dict
## @complexity 3
async def process_with_vlm(document: dict[str, Any]) -> dict[str, Any]:
    """Process document with external VLM to enrich results.

    VLM integration has moved to docling-serve via ENV variables.
    This function is now a pass-through for backward compatibility.

    Args:
        document: Document result from docling-serve.

    Returns:
        Document as-is (VLM already applied by docling-serve).
    """
    _log.info("[IMP:6][process_with_vlm][PASS] VLM handled by docling-serve, returning as-is")
    return document
# endregion FUNC_process_with_vlm


# region FUNC_extract_pages [DOMAIN(4): VLM; CONCEPT(4): Utility; TECH(4): dict]
## @purpose Stub для обратной совместимости. Больше не используется.
## @io dict -> list[dict]
## @complexity 2
def extract_pages(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract pages from docling-serve document format.

    DEPRECATED: VLM processing moved to docling-serve.
    """
    return []
# endregion FUNC_extract_pages


# DEPRECATED: All VLM processing moved to docling-serve via ENV variables
# Kept for import compatibility only
async def process_page_with_vlm(page: dict[str, Any], page_num: int) -> dict[str, Any]:
    """DEPRECATED: VLM now handled by docling-serve."""
    return page


async def call_vlm(image_data: dict[str, Any], page_num: int, img_idx: int) -> dict[str, Any]:
    """DEPRECATED: VLM now handled by docling-serve."""
    return {"error": "deprecated"}