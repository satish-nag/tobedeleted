# redis_client.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import redis


@dataclass(frozen=True)
class RedisConfig:
    host: str = "redis-13742.c85.us-east-1-2.ec2.cloud.redislabs.com"
    port: int = 13742
    db: int = 0
    password: Optional[str] = None

    # Use URL to avoid version-specific kwargs like `ssl=...`
    # Example:
    #   redis://localhost:6379/0
    #   rediss://localhost:6380/0
    url: Optional[str] = None

    socket_timeout_s: float = 2.0
    socket_connect_timeout_s: float = 2.0
    max_connections: int = 50


class RedisClient:
    """
    Compatible across redis-py versions by using Redis.from_url when possible.
    Avoids passing `ssl=` which can break depending on redis-py version.
    """
    def __init__(self, cfg: RedisConfig):
        if cfg.url:
            self._r = redis.Redis.from_url(
                cfg.url,
                password=cfg.password,
                socket_timeout=cfg.socket_timeout_s,
                socket_connect_timeout=cfg.socket_connect_timeout_s,
                max_connections=cfg.max_connections,
                decode_responses=False,
            )
        else:
            self._r = redis.Redis(
                host=cfg.host,
                port=cfg.port,
                db=cfg.db,
                password=cfg.password,
                socket_timeout=cfg.socket_timeout_s,
                socket_connect_timeout=cfg.socket_connect_timeout_s,
                decode_responses=False,
            )

    @property
    def raw(self) -> redis.Redis:
        return self._r

    def ping(self) -> bool:
        return bool(self._r.ping())