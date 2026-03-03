import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

log = structlog.get_logger()

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        clear_contextvars()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        bind_contextvars(
            request_id=request_id,
            path=request.url.path,
            method=request.method,
        )
        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            log.info(
                "http_request",
                status_code=response.status_code,
                elapsed_ms=elapsed_ms,
                client_host=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )

            response.headers["x-request-id"] = request_id
            return response
        except Exception:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            log.exception("http_request_failed", elapsed_ms=elapsed_ms)
            raise