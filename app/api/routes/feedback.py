from fastapi import APIRouter, Depends, Path
import structlog

from app.schemas.feedback import FeedbackRequest, FeedbackRecord
from app.api.deps import get_feedback_repo
from app.repositories.feedback_repo import InMemoryFeedbackRepository

log = structlog.get_logger()

router = APIRouter(prefix="/v1/alerts", tags=["feedback"])


@router.post(
    "/{alert_id}/summary/feedback",
    response_model=FeedbackRecord,
    summary="Submit summary feedback",
    description="Stores thumbs up/down with optional comment. Uses dummy in-memory storage for now.",
)
async def submit_feedback(
    payload: FeedbackRequest,
    alert_id: str = Path(..., description="Alert ID"),
    repo: InMemoryFeedbackRepository = Depends(get_feedback_repo),
):
    rec = await repo.save(alert_id=alert_id, req=payload)
    log.info("feedback_saved", alert_id=alert_id, rating=payload.rating, has_comment=bool(payload.comment))
    return rec