import time

from httpx import Headers
from structlog.contextvars import get_contextvars

import httpx
from app.core import settings
from app.core import UpstreamError
from app.schemas import AlertDetails
import structlog

log = structlog.get_logger()

def get_headers() -> dict[str, str]:
    ctx = get_contextvars()
    request_id = ctx.get("request_id")
    headers = {}
    if request_id:
        headers["x-request-id"] = request_id
    return headers

## TODO: require improvements after improvising the alert details model
class AlertDetailsClient:
    def __init__(self) -> None:
        self._timeout = httpx.Timeout(settings.http_timeout_seconds)

    async def get_alert_details(self, alert_id: str) -> AlertDetails:
        url = f"{settings.alert_details_url.rstrip('/')}/{alert_id}"
        start = time.time()
        async with httpx.AsyncClient(timeout=self._timeout, headers=get_headers()) as client:
            try:
                resp = await client.get(url)
            except httpx.RequestError as e:
                raise UpstreamError(f"Alert details request failed: {e}") from e

        if resp.status_code >= 400:
            raise UpstreamError(
                f"Alert details returned {resp.status_code}",
                status_code=resp.status_code,
            )

        data = resp.json()
        # Expect the upstream to return at least an alert_id; tolerate anything else.
        upstream_alert_id = str(data.get("alert_id") or alert_id)

        log.info("alert_details_fetched", alert_id=upstream_alert_id, bytes=len(resp.content),path=url,elapsed_time_ms=f"{int((time.time() - start)*1000)} ms.")
        return AlertDetails(alert_id=upstream_alert_id)

