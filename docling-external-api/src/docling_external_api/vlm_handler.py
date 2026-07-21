"""VLM (Vision Language Model) handler for enriching document results."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from docling_external_api.config import get_config

_log = logging.getLogger(__name__)


# region MODULE_CONTRACT [DOMAIN(8): VLM; CONCEPT(8): Vision, Language Model; TECH(9): httpx, OpenAI]
## @modulecontract
## @purpose Обрабатывать изображения документов через внешний VLM API.
## @scope Извлечение страниц, вызов VLM, обогащение результатов.
## @input Document result от docling-serve
## @output Enriched document с VLM результатами
## @links [USES_API(8): httpx]
## @invariants
## - VLM вызывается только если включен в конфигурации
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
## @modulemap
## FUNC 8[Process document with VLM] => process_with_vlm
## FUNC 7[Extract pages from doc] => extract_pages
## FUNC 8[Call VLM API] => call_vlm
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: VLM, vision, language model, image processing, external API, minimax
# STRUCTURE: ▶ DocResult → ○ Extract Pages → ⚡ Call VLM API → ⊕ Merge Results → ⎋ EnrichedDoc


# region FUNC_process_with_vlm [DOMAIN(8): VLM; CONCEPT(8): Processing; TECH(9): httpx]
## @purpose Обработать документ через VLM для обогащения результатов.
## @uses ExternalApiConfig, call_vlm
## @io dict -> dict
## @complexity 8
async def process_with_vlm(document: dict[str, Any]) -> dict[str, Any]:
    """Process document with external VLM to enrich results.

    Args:
        document: Document result from docling-serve.

    Returns:
        Document with VLM enrichments added.
    """
    config = get_config()

    if not config.vlm_enabled:
        _log.info("[IMP:6][process_with_vlm][SKIP] VLM not enabled, returning original")
        return document

    _log.info(f"[IMP:7][process_with_vlm][START] Processing document with VLM model={config.vlm_model}")

    pages = extract_pages(document)

    if not pages:
        _log.info("[IMP:6][process_with_vlm][NO_PAGES] No pages found in document")
        return document

    _log.info(f"[IMP:7][process_with_vlm][PAGES] Found {len(pages)} pages to process")

    enriched_pages = []
    for i, page in enumerate(pages):
        _log.debug(f"[IMP:5][process_with_vlm][PAGE] Processing page {i + 1}/{len(pages)}")
        enriched_page = await process_page_with_vlm(page, i)
        enriched_pages.append(enriched_page)

    _log.info(f"[IMP:8][process_with_vlm][COMPLETE] Processed {len(enriched_pages)} pages")
    return document
# endregion FUNC_process_with_vlm


# region FUNC_extract_pages [DOMAIN(7): VLM; CONCEPT(6): Extraction; TECH(8): dict]
## @purpose Извлечь страницы из документа docling-serve.
## @io dict -> list[dict]
## @complexity 5
def extract_pages(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract pages from docling-serve document format.

    Args:
        document: Document dict from docling-serve response.

    Returns:
        List of page dicts.
    """
    if not document:
        return []

    if "pages" in document:
        return document.get("pages", [])

    if "documents" in document:
        docs = document.get("documents", [])
        if docs and "pages" in docs[0]:
            return docs[0].get("pages", [])

    _log.debug("[IMP:5][extract_pages][UNKNOWN] Document format not recognized")
    return []
# endregion FUNC_extract_pages


# region FUNC_process_page_with_vlm [DOMAIN(8): VLM; CONCEPT(7): Page Processing; TECH(9): httpx]
## @purpose Обработать одну страницу через VLM API.
## @uses call_vlm
## @io dict, int -> dict
## @complexity 7
async def process_page_with_vlm(page: dict[str, Any], page_num: int) -> dict[str, Any]:
    """Process a single page with VLM API.

    Args:
        page: Page dict from document.
        page_num: Page number for logging.

    Returns:
        Page dict with VLM enrichment added.
    """
    config = get_config()

    images = page.get("images", [])
    if not images:
        _log.debug(f"[IMP:5][process_page_with_vlm][PAGE:{page_num}] No images in page")
        return page

    _log.debug(f"[IMP:6][process_page_with_vlm][PAGE:{page_num}] Found {len(images)} images")

    vlm_results = []
    for img_idx, image in enumerate(images):
        _log.debug(f"[IMP:6][process_page_with_vlm][PAGE:{page_num}][IMG:{img_idx}] Calling VLM")
        result = await call_vlm(image, page_num, img_idx)
        vlm_results.append(result)

    page["vlm_results"] = vlm_results
    return page
# endregion FUNC_process_page_with_vlm


# region FUNC_call_vlm [DOMAIN(9): VLM; CONCEPT(8): API Call; TECH(9): httpx]
## @purpose Вызвать внешний VLM API для обработки изображения.
## @uses ExternalApiConfig
## @io dict, int, int -> dict
## @complexity 8
async def call_vlm(image_data: dict[str, Any], page_num: int, img_idx: int) -> dict[str, Any]:
    """Call external VLM API for image processing.

    Args:
        image_data: Image data dict (contains base64 or URL).
        page_num: Page number for logging.
        img_idx: Image index for logging.

    Returns:
        VLM response as dict.
    """
    config = get_config()

    if not config.vlm_enabled:
        return {"error": "VLM not enabled"}

    _log.info(
        f"[IMP:7][call_vlm][PAGE:{page_num}][IMG:{img_idx}] "
        f"Calling VLM: {config.vlm_model} at {config.vlm_base_url}"
    )

    prompt = "Describe this document page in detail, focusing on text content, tables, and structure."

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data.get('base64', '')}"}},
            ],
        }
    ]

    payload = {
        "model": config.vlm_model,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 4096,
    }

    headers = {
        "Content-Type": "application/json",
    }
    if config.vlm_api_key:
        headers["Authorization"] = f"Bearer {config.vlm_api_key}"

    try:
        async with httpx.AsyncClient(timeout=config.vlm_timeout) as client:
            response = await client.post(
                f"{config.vlm_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

            _log.info(
                f"[IMP:8][call_vlm][PAGE:{page_num}][IMG:{img_idx}] "
                f"VLM response received, tokens={result.get('usage', {}).get('total_tokens', 'N/A')}"
            )
            return result

    except httpx.TimeoutException:
        _log.warning(f"[IMP:7][call_vlm][PAGE:{page_num}][IMG:{img_idx}] VLM timeout")
        return {"error": "VLM request timed out"}
    except httpx.HTTPStatusError as e:
        _log.warning(f"[IMP:7][call_vlm][PAGE:{page_num}][IMG:{img_idx}] VLM HTTP error: {e}")
        return {"error": f"VLM HTTP {e.response.status_code}"}
    except Exception as e:
        _log.error(f"[IMP:8][call_vlm][PAGE:{page_num}][IMG:{img_idx}] VLM error: {e}")
        return {"error": str(e)}
# endregion FUNC_call_vlm