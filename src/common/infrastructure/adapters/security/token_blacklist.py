from redis.asyncio import Redis

from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService

KEY_PREFIX = "blacklist:"


class RedisTokenBlacklistService(ITokenBlacklistService):
    """Stores revoked token IDs (jti) in Redis with TTL matching the token's
    remaining validity.

    Keys are auto-expired by Redis once the token would have naturally
    expired, keeping the blacklist size bounded.
    """

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def blacklist(self, jti: str, ttl: int) -> None:
        key = f"{KEY_PREFIX}{jti}"
        await self.redis.set(key, "1", ex=ttl)

    async def is_blacklisted(self, jti: str) -> bool:
        key = f"{KEY_PREFIX}{jti}"
        result = await self.redis.exists(key)
        return result > 0
