# cache_store.py
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from redis_client import RedisClient


@dataclass(frozen=True)
class CacheStore:
    client: RedisClient
    key_prefix: str = "app:cache:"

    def _k(self, key: str) -> str:
        return f"{self.key_prefix}{key}"

    def set_json(self, key: str, value: Any, ttl_s: Optional[int] = None) -> None:
        payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        k = self._k(key)
        r = self.client.raw
        if ttl_s is None:
            r.set(k, payload)
        else:
            r.set(k, payload, ex=int(ttl_s))

    def get_json(self, key: str) -> Optional[Any]:
        data = self.client.raw.get(self._k(key))
        if data is None:
            return None
        try:
            return json.loads(data.decode("utf-8"))
        except Exception:
            return None

    def delete(self, key: str) -> int:
        return int(self.client.raw.delete(self._k(key)))

    def exists(self, key: str) -> bool:
        return bool(self.client.raw.exists(self._k(key)))