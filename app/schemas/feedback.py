from pydantic import BaseModel, Field
from typing import Optional, Literal

"""
Improvised later once we finalize the on the feedback
"""
class FeedbackRequest(BaseModel):
    rating: Literal["up", "down"] = Field(..., description="Thumbs up/down")
    comment: Optional[str] = Field(default=None, max_length=2000)


class FeedbackRecord(BaseModel):
    alert_id: str
    rating: str
    comment: Optional[str] = None
    created_at_iso: str