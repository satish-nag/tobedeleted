from fastapi import FastAPI, Request
import structlog

from app.core import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.api.routes import all_routers
from app.core.config import settings
from app.core.exception_handlers import (
    UpstreamError, upstream_error_handler, llm_error_handler, validation_error_handler,LLMError,ValidationAppError
)

## configure logging
configure_logging()
log = structlog.get_logger()

## Create Fast API instance
app = FastAPI(
    title="Alert Summary API",
    version="0.1.0",
    description=(
        "Streams LLM-generated summaries for fraud alerts. "
        "Uses Alert Details API + Azure OpenAI (LangChain)."
    ),

)

## Add middleware
app.add_middleware(RequestContextMiddleware)

## add all endpoints to the app
for r in all_routers:
    app.include_router(r)

## add exception handlers
app.add_exception_handler(UpstreamError, upstream_error_handler)
app.add_exception_handler(LLMError, llm_error_handler)
app.add_exception_handler(ValidationAppError, validation_error_handler)


@app.get("/", include_in_schema=False)
async def root():
    return {"name": settings.app_name, "env": settings.env}