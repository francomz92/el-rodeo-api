from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis

from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.common.infrastructure.adapters.security.token_blacklist import (
    RedisTokenBlacklistService,
)
from src.common.infrastructure.core import settings

# ── Shared Redis connection (connection pool managed by from_url) ─────
# Created once at import time and reused across requests. The pool is
# closed when the event loop shuts down (Redis handles this gracefully).
_redis_client: Redis = Redis.from_url(settings.REDIS_URL)


async def _get_redis_client() -> Redis:
    """Yield the shared Redis connection.

    Uses a module-level singleton to avoid creating a new TCP connection
    (and connection pool) per request. The pool is managed by redis-py
    internally — connections are borrowed and returned transparently.
    """
    yield _redis_client


def _get_blacklist_service(
    redis: Annotated[Redis, Depends(_get_redis_client)],
) -> ITokenBlacklistService:
    return RedisTokenBlacklistService(redis)


GetRedisClient = Annotated[Redis, Depends(_get_redis_client)]
GetTokenBlacklistService = Annotated[
    ITokenBlacklistService,
    Depends(_get_blacklist_service),
]
