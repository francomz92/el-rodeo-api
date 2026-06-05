from typing import Annotated, AsyncGenerator

from fastapi import Depends

from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.common.infrastructure.adapters.security.token_blacklist import (
    RedisTokenBlacklistService,
)
from src.common.infrastructure.persistence.connections.redis import Redis, _redis_client


async def _get_redis_client() -> AsyncGenerator[Redis, None]:
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
