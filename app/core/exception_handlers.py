from fastapi import Request
from fastapi.responses import JSONResponse
import structlog

from app.core.errors import UpstreamError, LLMError, ValidationAppError

log = structlog.get_logger()


async def upstream_error_handler(request: Request, exc: UpstreamError):
    log.warning(
        "upstream_error",
        detail=str(exc),
        upstream_status=exc.status_code,
    )
    return JSONResponse(
        status_code=502,
        content={
            "error": "upstream_error",
            "detail": str(exc),
            "upstream_status": exc.status_code,
        },
    )


async def llm_error_handler(request: Request, exc: LLMError):
    log.warning("llm_error", detail=str(exc))
    return JSONResponse(
        status_code=502,
        content={"error": "llm_error", "detail": str(exc)},
    )


async def validation_error_handler(request: Request, exc: ValidationAppError):
    log.info("validation_error", detail=str(exc))
    return JSONResponse(
        status_code=400,
        content={"error": "validation_error", "detail": str(exc)},
    )