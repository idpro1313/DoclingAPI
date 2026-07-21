"""FastAPI main entry point for docling-external-api standalone service."""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from src.config import get_config
from src.models import (
    ConvertSourceRequest,
    ConvertSourceResponse,
    HealthResponse,
)
from src.proxy import convert_document, health_check as check_downstream
from src.vlm_handler import process_with_vlm

_log = logging.getLogger(__name__)


# region MODULE_CONTRACT [DOMAIN(9): Server; CONCEPT(8): FastAPI, Entry Point; TECH(9): uvicorn, fastapi]
## @modulecontract
## @purpose Standalone FastAPI сервер для docling-external-api.
## @scope HTTP API, проксирование, VLM обработка.
## @input HTTP requests от клиентов
## @output JSON responses
## @links [USES_API(9): uvicorn, fastapi]
## @invariants
## - Lifespan context управляет startup/shutdown
## @changes
## LAST_CHANGE: v0.3.0 - Standalone service architecture
## @modulemap
## FUNC 9[Main FastAPI app] => app
## FUNC 8[Conversion endpoint] => convert_source
## FUNC 5[Health endpoint] => health
def _module_contract():
    pass
# endregion MODULE_CONTRACT
# GREP_SUMMARY: FastAPI, uvicorn, server, entry point, standalone service
# STRUCTURE: ▶ Init ┌Config┐ → ○ FastAPI App → ○ Routes → ⚡ Start Server → ⎋ serve


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    config = get_config()

    _log.info(f"[IMP:8][lifespan][STARTUP] docling-external-api v0.3.0 starting")
    _log.info(f"[IMP:7][lifespan][CONFIG] docling_serve_url={config.docling_serve_url}")
    _log.info(f"[IMP:7][lifespan][CONFIG] vlm_enabled={config.vlm_enabled}")
    _log.info(f"[IMP:7][lifespan][CONFIG] vlm_model={config.vlm_model}")
    _log.info(f"[IMP:7][lifespan][CONFIG] port={config.api_port}")

    upstream_healthy = await check_downstream()
    if upstream_healthy:
        _log.info("[IMP:7][lifespan][STARTUP] docling-serve is reachable")
    else:
        _log.warning("[IMP:6][lifespan][STARTUP] docling-serve is NOT reachable (will retry on requests)")

    yield

    _log.info("[IMP:7][lifespan][SHUTDOWN] docling-external-api shutting down")


app = FastAPI(
    title="docling-external-api",
    description="Standalone service for external API integration with docling-serve",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# region FUNC_convert_source [DOMAIN(9): API; CONCEPT(8): Conversion; TECH(9): fastapi]
## @purpose POST /v1/convert/source endpoint - proxy and enrich document conversion.
## @uses convert_document, process_with_vlm
## @io ConvertSourceRequest -> ConvertSourceResponse
## @complexity 8
@app.post("/v1/convert/source", response_model=ConvertSourceResponse)
async def convert_source(request: ConvertSourceRequest) -> ConvertSourceResponse:
    """Convert document source via docling-serve with optional VLM enrichment.

    Request body:
    ```json
    {
        "sources": [{"kind": "url", "uri": "https://example.com/doc.pdf"}]
    }
    ```

    Returns:
        Converted document with optional VLM enrichments.
    """
    _log.info("[IMP:7][convert_source][REQUEST] Received conversion request")

    try:
        request_dict = request.model_dump(mode="json", exclude_none=True)
        _log.debug(f"[IMP:6][convert_source][DEBUG] Request: {request_dict}")

        _log.info("[IMP:7][convert_source][PROXY] Forwarding to docling-serve")
        docling_result = await convert_document(request_dict)

        _log.info("[IMP:7][convert_source][VLM] Processing with VLM if enabled")
        enriched_result = await process_with_vlm(docling_result)

        _log.info("[IMP:8][convert_source][COMPLETE] Conversion successful")
        return ConvertSourceResponse(status="success", document=enriched_result)

    except Exception as e:
        _log.error(f"[IMP:9][convert_source][ERROR] Conversion failed: {e}")
        return ConvertSourceResponse(
            status="error",
            error=str(e),
        )
# endregion FUNC_convert_source


# region FUNC_health [DOMAIN(5): API; CONCEPT(5): Health; TECH(7): fastapi]
## @purpose GET /health endpoint - service health check.
## @io None -> HealthResponse
## @complexity 3
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    config = get_config()
    downstream_healthy = await check_downstream()

    return HealthResponse(
        status="healthy" if downstream_healthy else "degraded",
        version="0.3.0",
        docling_serve_url=config.docling_serve_url,
        vlm_enabled=config.vlm_enabled,
    )
# endregion FUNC_health


@app.get("/ui")
async def ui_redirect():
    """Redirect to docling-serve UI."""
    config = get_config()
    return RedirectResponse(url=f"{config.docling_serve_url}/ui")


@app.get("/docs")
async def docs_redirect():
    """Redirect to docling-serve API docs."""
    config = get_config()
    return RedirectResponse(url=f"{config.docling_serve_url}/docs")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    _log.error(f"[IMP:9][exception_handler][UNHANDLED] {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "error": "Internal server error"},
    )


def main():
    """Main entry point for running the service."""
    config = get_config()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    _log.info(f"[IMP:6][main][START] Starting server on port {config.api_port}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.api_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()