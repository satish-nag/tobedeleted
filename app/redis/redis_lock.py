# redis_lock.py
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional

from redis_client import RedisClient

_UNLOCK_LUA = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("DEL", KEYS[1])
else
  return 0
end
"""


class LockNotAcquired(Exception):
    pass


@dataclass
class RedisLock:
    client: RedisClient
    name: str
    ttl_ms: int = 30_000
    key_prefix: str = "app:lock:"

    def __post_init__(self) -> None:
        self._token: Optional[bytes] = None
        self._key: str = f"{self.key_prefix}{self.name}"
        self._unlock = self.client.raw.register_script(_UNLOCK_LUA)

    def acquire(
        self,
        blocking: bool = True,
        timeout_s: float = 10.0,
        retry_interval_s: float = 0.05,
        jitter_s: float = 0.05,
    ) -> "RedisLock":
        start = time.monotonic()
        r = self.client.raw
        token = uuid.uuid4().hex.encode("utf-8")

        def try_once() -> bool:
            return bool(r.set(self._key, token, nx=True, px=int(self.ttl_ms)))

        if not blocking:
            if not try_once():
                raise LockNotAcquired(f"Lock busy: {self._key}")
            self._token = token
            return self

        while True:
            if try_once():
                self._token = token
                return self

            if (time.monotonic() - start) >= timeout_s:
                raise LockNotAcquired(f"Timed out acquiring lock: {self._key}")

            time.sleep(retry_interval_s + (uuid.uuid4().int % int(jitter_s * 1000 + 1)) / 1000.0)

    def release(self) -> bool:
        if self._token is None:
            return False
        try:
            res = self._unlock(keys=[self._key], args=[self._token])
            return bool(res == 1)
        finally:
            self._token = None

    def __enter__(self) -> "RedisLock":
        if self._token is None:
            self.acquire(blocking=True)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()