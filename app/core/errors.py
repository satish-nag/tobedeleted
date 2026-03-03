from __future__ import annotations


class AppError(Exception):
    """Base application error."""


class UpstreamError(AppError):
    """Error calling upstream services (alert details, LLM, etc.)."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ValidationAppError(AppError):
    """Request/response validation error."""


class LLMError(AppError):
    """LLM invocation error."""