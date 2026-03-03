### TODO: placeholder for storing the feedback
### TODO: replace the in memory storage with appropriate storage in future
from __future__ import annotations
from typing import Protocol, List
from datetime import datetime, timezone
from app.schemas import FeedbackRequest, FeedbackRecord


class FeedbackRepository(Protocol):
    async def save(self, alert_id: str, req: FeedbackRequest) -> FeedbackRecord: ...
    async def list_for_alert(self, alert_id: str) -> List[FeedbackRecord]: ...


class InMemoryFeedbackRepository:
    def __init__(self) -> None:
        self._rows: list[FeedbackRecord] = []

    async def save(self, alert_id: str, req: FeedbackRequest) -> FeedbackRecord:
        rec = FeedbackRecord(
            alert_id=alert_id,
            rating=req.rating,
            comment=req.comment,
            created_at_iso=datetime.now(timezone.utc).isoformat(),
        )
        self._rows.append(rec)
        return rec

    async def list_for_alert(self, alert_id: str) -> list[FeedbackRecord]:
        return [r for r in self._rows if r.alert_id == alert_id]