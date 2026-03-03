from functools import lru_cache
from app.services import AlertDetailsClient
from app.repositories import InMemoryFeedbackRepository
from app.agent.alert_summary import AlertSummary


@lru_cache
def get_alert_client() -> AlertDetailsClient:
    return AlertDetailsClient()


@lru_cache
def get_feedback_repo() -> InMemoryFeedbackRepository:
    return InMemoryFeedbackRepository()

@lru_cache
def get_summary_service():
    return AlertSummary()