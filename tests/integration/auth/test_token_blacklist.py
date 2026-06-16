"""Integration tests for the Redis-backed token blacklist.

Tests the port interface directly against real Redis so we catch
connection issues, key-expiry problems, and data-format mismatches.

Each test creates its own Redis connection to avoid event-loop conflicts
(pytest-asyncio 1.4 uses session-scope event loop for fixtures but
function-scope for tests). Connections are closed via try/finally.
"""

import asyncio

import pytest
from redis.asyncio import Redis

from src.common.infrastructure.adapters.security.token_blacklist import (
    RedisTokenBlacklistService,
)
from src.common.infrastructure.core import settings


@pytest.mark.asyncio
class TestRedisTokenBlacklist:
    async def _make_service(self) -> tuple[RedisTokenBlacklistService, Redis]:
        """Create a Redis client, flush, and return a service + client pair.

        The caller is responsible for calling ``await redis.aclose()``
        (typically via try/finally in the test body).
        """
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.flushdb()
        return RedisTokenBlacklistService(redis), redis

    async def test_blacklist_and_check(self):
        service, redis = await self._make_service()
        try:
            assert await service.is_blacklisted("jti-1") is False

            await service.blacklist("jti-1", ttl=60)
            assert await service.is_blacklisted("jti-1") is True
        finally:
            await redis.aclose()

    async def test_absent_jti_returns_false(self):
        service, redis = await self._make_service()
        try:
            assert await service.is_blacklisted("nonexistent-jti") is False
        finally:
            await redis.aclose()

    async def test_ttl_expires_key(self):
        service, redis = await self._make_service()
        try:
            await service.blacklist("short-lived", ttl=1)
            assert await service.is_blacklisted("short-lived") is True

            await asyncio.sleep(1.1)
            assert await service.is_blacklisted("short-lived") is False
        finally:
            await redis.aclose()

    async def test_multiple_blacklisted_tokens(self):
        service, redis = await self._make_service()
        try:
            for jti in ["a", "b", "c"]:
                await service.blacklist(jti, ttl=120)

            assert await service.is_blacklisted("a") is True
            assert await service.is_blacklisted("b") is True
            assert await service.is_blacklisted("c") is True
            assert await service.is_blacklisted("d") is False
        finally:
            await redis.aclose()
