from redis.asyncio import Redis

from src.common.infrastructure.core import settings

_redis_client: Redis = Redis.from_url(settings.REDIS_URL)
