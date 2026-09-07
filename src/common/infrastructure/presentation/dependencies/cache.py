from typing import Annotated

from fastapi import Depends

from src.common.domain.ports.cache_service import ICacheService
from src.common.infrastructure.adapters.cache_service import RedisCacheService
from src.common.infrastructure.presentation.dependencies.redis import GetRedisClient


def _get_cache_service(redis: GetRedisClient) -> ICacheService:  # type: ignore[reportInvalidTypeForm]
    """Build a Redis-backed cache service."""
    return RedisCacheService(redis=redis)


GetCacheService = Annotated[ICacheService, Depends(_get_cache_service)]
