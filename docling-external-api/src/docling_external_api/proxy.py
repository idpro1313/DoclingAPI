"""HTTP proxy module for forwarding requests to docling-serve."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from docling_external_api.config import get_config

_log = logging.getLogger(__name__)


# region MODULE_CONTRACT [DOMAIN(8): Proxy; CONCEPT(7): HTTP, Forwarding; TECH(9): httpx]
## @modulecontract
## @purpose Проксировать запросы клиентов в docling-serve и возвращать результаты.
## @scope POST /v1/convert/source, GET /health
## @input HTTP request от клиента
## @output Response от docling-serve
## @links [USES_API(9): httpx]
## @invariants
## - Прокси работает асинхронно
## - Timeout применяется к каждому запросу
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
## @modulemap
## FUNC 8[Convert document via proxy] => convert_document
## FUNC 6[Check downstream health] => health_check
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: Proxy, HTTP, httpx, docling-serve, forward, convert
# STRUCTURE: ▶ Client Request → ○ Build target URL → ⚡ httpx.post → ⊕ Response → ⎋ return


# region FUNC_convert_document [DOMAIN(8): Proxy; CONCEPT(8): Conversion; TECH(9): httpx]
## @purpose Проксировать запрос конвертации документа в docling-serve.
## @uses httpx.AsyncClient, ExternalApiConfig
## @io dict -> dict
## @complexity 7
async def convert_document(request_data: dict[str, Any]) -> dict[str, Any]:
    """Convert document by proxying request to docling-serve.

    Args:
        request_data: Request body for conversion endpoint.

    Returns:
        Response from docling-serve as dict.

    Raises:
        httpx.HTTPError: If request to docling-serve fails.
    """
    config = get_config()
    target_url = f"{config.docling_serve_url}/v1/convert/source"

    _log.info(f"[IMP:7][convert_document][PROXY] Forwarding to: {target_url}")

    timeout = request_data.get("timeout", 120.0)
    max_num_images = request_data.get("max_num_images", 10)

    _log.info(f"[IMP:7][convert_document][CONFIG] timeout={timeout}, max_num_images={max_num_images}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            _log.info(f"[IMP:8][convert_document][REQUEST] Sending request to docling-serve")
            response = await client.post(
                target_url,
                json=request_data,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

            _log.info(
                f"[IMP:8][convert_document][RESPONSE] Status: {response.status_code}, "
                f"Size: {len(response.content)} bytes"
            )

            return response.json()

        except httpx.TimeoutException as e:
            _log.error(f"[IMP:9][convert_document][TIMEOUT] Request timed out: {e}")
            raise
        except httpx.HTTPStatusError as e:
            _log.error(f"[IMP:9][convert_document][HTTP_ERROR] HTTP {e.response.status_code}: {e}")
            raise
        except httpx.RequestError as e:
            _log.error(f"[IMP:9][convert_document][REQUEST_ERROR] Connection failed: {e}")
            raise
# endregion FUNC_convert_document


# region FUNC_health_check [DOMAIN(6): Proxy; CONCEPT(5): Health; TECH(8): httpx]
## @purpose Проверить доступность docling-serve.
## @uses httpx.AsyncClient
## @io None -> bool
## @complexity 5
async def health_check() -> bool:
    """Check if docling-serve is reachable.

    Returns:
        True if docling-serve returns 200, False otherwise.
    """
    config = get_config()
    target_url = f"{config.docling_serve_url}/health"

    _log.debug(f"[IMP:5][health_check][CHECK] Testing: {target_url}")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(target_url)
            is_healthy = response.status_code == 200

            _log.debug(
                f"[IMP:6][health_check][RESULT] docling-serve: {'healthy' if is_healthy else 'unhealthy'}"
            )
            return is_healthy

    except Exception as e:
        _log.warning(f"[IMP:6][health_check][ERROR] Failed to reach docling-serve: {e}")
        return False
# endregion FUNC_health_check