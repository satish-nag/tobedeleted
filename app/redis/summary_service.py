# summary_service.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from cache_store import CacheStore
from redis_client import RedisClient
from redis_lock import RedisLock, LockNotAcquired


def summary_cache_key(alert_id: str) -> str:
    return f"alert:{alert_id}:summary"


@dataclass
class AlertSummaryService:
    redis_client: RedisClient
    cache: CacheStore

    lock_ttl_ms: int = 60_000
    in_progress_ttl_s: int = 10 * 60
    completed_ttl_s: int = 60 * 60
    error_ttl_s: int = 10 * 60

    def _now_epoch(self) -> int:
        return int(time.time())

    def _lock_name(self, alert_id: str) -> str:
        return f"alert:{alert_id}:summary:lock"

    def _set_record(
        self,
        alert_id: str,
        *,
        status: str,
        summary: Optional[Any] = None,
        error: Optional[str] = None,
        ttl_s: Optional[int] = None,
    ) -> None:
        self.cache.set_json(
            summary_cache_key(alert_id),
            {
                "status": status,
                "summary": summary,
                "error": error,
                "last_updated_epoch": self._now_epoch(),
            },
            ttl_s=ttl_s,
        )

    def start_generation_if_needed(
        self,
        alert_id: str,
        generator_fn: Callable[[], Dict[str, Any]],
    ) -> bool:
        record = self.cache.get_json(summary_cache_key(alert_id))
        if (
            isinstance(record, dict)
            and record.get("status") == "COMPLETED"
            and record.get("summary") is not None
        ):
            return False

        lock = RedisLock(
            client=self.redis_client,
            name=self._lock_name(alert_id),
            ttl_ms=self.lock_ttl_ms,
        )

        try:
            lock.acquire(blocking=False)
        except LockNotAcquired:
            return False

        try:
            self._set_record(alert_id, status="IN_PROGRESS", ttl_s=self.in_progress_ttl_s)

            try:
                summary = generator_fn()
            except Exception as e:
                self._set_record(alert_id, status="ERROR", error=str(e), ttl_s=self.error_ttl_s)
                return True

            self._set_record(
                alert_id,
                status="COMPLETED",
                summary=summary,
                error=None,
                ttl_s=self.completed_ttl_s,
            )
            return True
        finally:
            lock.release()

    def get_summary_or_wait(
        self,
        alert_id: str,
        wait_timeout_s: float = 20.0,
        poll_interval_s: float = 0.25,
        max_poll_interval_s: float = 1.5,
        backoff_factor: float = 1.35,
    ) -> Dict[str, Any]:
        deadline = time.monotonic() + wait_timeout_s
        interval = poll_interval_s

        while True:
            record = self.cache.get_json(summary_cache_key(alert_id))

            if isinstance(record, dict):
                status = record.get("status")
                if status == "COMPLETED" and record.get("summary") is not None:
                    return record
                if status == "ERROR":
                    if not record.get("error"):
                        record["error"] = "Unknown error"
                    return record

            if time.monotonic() >= deadline:
                return {
                    "status": "TIMEOUT",
                    "summary": None,
                    "error": "Timed out waiting for summary",
                    "last_updated_epoch": self._now_epoch(),
                }

            time.sleep(interval)
            interval = min(max_poll_interval_s, interval * backoff_factor)
