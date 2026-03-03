from pydantic import BaseModel, Field

class AlertDetails(BaseModel):
    """
    Alert details passed to LLM TODO: add later
    """
    alert_id: str = Field(..., description="Unique alert identifier")