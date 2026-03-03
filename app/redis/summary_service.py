# summary_service.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Callable

from cache_store import CacheStore
from redis_client import RedisClient
from redis_lock import RedisLock, LockNotAcquired


@dataclass(frozen=True)
class SummaryKeys:
    status: str
    summary: str
    error: str


def make_summary_keys(alert_id: str) -> SummaryKeys:
    base = f"alert:{alert_id}:summary"
    return SummaryKeys(
        status=f"{base}:status",
        summary=f"{base}:data",
        error=f"{base}:error",
    )


@dataclass
class AlertSummaryService:
    redis_client: RedisClient
    cache: CacheStore

    lock_ttl_ms: int = 60_000
    in_progress_ttl_s: int = 10 * 60
    completed_ttl_s: int = 60 * 60
    error_ttl_s: int = 10 * 60

    def _lock_name(self, alert_id: str) -> str:
        return f"alert:{alert_id}:summary:lock"

    def start_generation_if_needed(
        self,
        alert_id: str,
        generator_fn: Callable[[], Dict[str, Any]],
    ) -> bool:
        keys = make_summary_keys(alert_id)

        status = self.cache.get_json(keys.status)
        if status and status.get("state") == "COMPLETED":
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
            self.cache.set_json(
                keys.status,
                {"state": "IN_PROGRESS", "updated_at_ms": int(time.time() * 1000)},
                ttl_s=self.in_progress_ttl_s,
            )

            try:
                summary = generator_fn()
            except Exception as e:
                self.cache.set_json(
                    keys.error,
                    {"message": str(e), "updated_at_ms": int(time.time() * 1000)},
                    ttl_s=self.error_ttl_s,
                )
                self.cache.set_json(
                    keys.status,
                    {"state": "ERROR", "updated_at_ms": int(time.time() * 1000)},
                    ttl_s=self.error_ttl_s,
                )
                return True

            self.cache.set_json(keys.summary, summary, ttl_s=self.completed_ttl_s)
            self.cache.set_json(
                keys.status,
                {"state": "COMPLETED", "updated_at_ms": int(time.time() * 1000)},
                ttl_s=self.completed_ttl_s,
            )
            self.cache.delete(keys.error)
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
        keys = make_summary_keys(alert_id)
        deadline = time.monotonic() + wait_timeout_s
        interval = poll_interval_s

        while True:
            status = self.cache.get_json(keys.status)

            if status is not None:
                state = status.get("state")
                if state == "COMPLETED":
                    summary = self.cache.get_json(keys.summary)
                    if summary is not None:
                        return {"state": "COMPLETED", "summary": summary}
                elif state == "ERROR":
                    err = self.cache.get_json(keys.error) or {"message": "Unknown error"}
                    return {"state": "ERROR", "error": err}

            if time.monotonic() >= deadline:
                return {"state": "TIMEOUT", "error": {"message": "Timed out waiting for summary"}}

            time.sleep(interval)
            interval = min(max_poll_interval_s, interval * backoff_factor)