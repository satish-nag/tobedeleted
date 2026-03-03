from fastapi import APIRouter, Depends, Path, Query
from starlette.responses import StreamingResponse
import asyncio
import structlog

from app.core import settings
from app.api import get_summary_service
from app.agent.alert_summary import AlertSummary
from app.api import get_alert_client

log = structlog.get_logger()

router = APIRouter(prefix="/v1/alerts", tags=["summaries"])


def _as_sse(text: str) -> str:
    # Simple Server-Sent Events framing (works well for streaming to UI)
    return f"data: {text}\n\n"


@router.get(
    "/{alert_id}/summary/stream",
    summary="Stream alert summary",
    description="Fetches alert details, calls LLM, streams back markdown via SSE.",
)
async def stream_summary(
    alert_id: str = Path(..., description="Alert ID"),
    svc: AlertSummary = Depends(get_summary_service),
):
    alertDetails = await get_alert_client().get_alert_details(alert_id)
    async def event_gen():
        # Optional initial event
        yield _as_sse("[START]\n")
        async for chunk in svc.getSummary(alertdetails=alertDetails):
            if settings.stream_chunk_sleep_ms > 0:
                await asyncio.sleep(settings.stream_chunk_sleep_ms / 1000)
            yield _as_sse(chunk)
        yield _as_sse("\n[END]")

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post(
    "/{alert_id}/summary/regenerate/stream",
    summary="Regenerate + stream alert summary",
    description="Same as stream endpoint but semantically used by UI to regenerate.",
)
async def regenerate_summary(
    alert_id: str = Path(..., description="Alert ID"),
    svc: AlertSummary = Depends(get_summary_service),
):
    # Currently same behavior; later you can invalidate cache, store version, etc.
    alertDetails = await get_alert_client().get_alert_details(alert_id)
    async def event_gen():
        yield _as_sse("[REGENERATE_START]\n")
        async for chunk in svc.getSummary(alertdetails=alertDetails):
            yield _as_sse(chunk)
        yield _as_sse("\n[REGENERATE_END]")

    return StreamingResponse(event_gen(), media_type="text/event-stream")