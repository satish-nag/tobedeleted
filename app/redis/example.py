# example.py
from __future__ import annotations

import threading
import time
from typing import Dict, Any

from redis_client import RedisClient, RedisConfig
from cache_store import CacheStore
from summary_service import AlertSummaryService


def mock_llm_call(alert_id: str) -> Dict[str, Any]:
    time.sleep(4)
    return {
        "alert_id": alert_id,
        "title": "Suspicious behavior detected",
        "summary": "User exhibited unusual transaction velocity and device changes.",
        "risk_score": 87,
    }


def rcm_event_fire_and_forget(service: AlertSummaryService, alert_id: str) -> None:
    did_generate = service.start_generation_if_needed(
        alert_id=alert_id,
        generator_fn=lambda: mock_llm_call(alert_id),
    )
    print(f"[RCM_EVENT] did_generate={did_generate}")


def ui_widget_call(service: AlertSummaryService, alert_id: str) -> None:
    result = service.get_summary_or_wait(alert_id=alert_id, wait_timeout_s=15)
    print(f"[UI_WIDGET] result={result}")


if __name__ == "__main__":
    # IMPORTANT:
    # - Use `url="redis://..."` if you need TLS, use `rediss://...`
    # - This avoids redis-py version differences around `ssl=` kwargs.
    client = RedisClient(RedisConfig(password="<password>"))

    assert client.ping()

    cache = CacheStore(client=client, key_prefix="rcm:")
    service = AlertSummaryService(redis_client=client, cache=cache)

    alert_id = "A-10001"

    t1 = threading.Thread(target=rcm_event_fire_and_forget, args=(service, alert_id), daemon=True)
    t2 = threading.Thread(target=ui_widget_call, args=(service, alert_id), daemon=True)

    t1.start()
    time.sleep(0.2)
    t2.start()

    t1.join()
    t2.join()

    print("[UI_WIDGET_2] result=", service.get_summary_or_wait(alert_id=alert_id, wait_timeout_s=2))