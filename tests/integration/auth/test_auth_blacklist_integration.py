"""Integration tests for AuthService with a real Redis-backed blacklist.

These tests verify that:
1. A valid token passes the blacklist check.
2. After blacklisting, the same token is rejected with UnauthorizedError.
3. Tokens without a jti claim (backward compatibility) still work.

Each test creates its own Redis connection to avoid event-loop conflicts.
Connections are closed via try/finally.
"""

from datetime import timedelta

import jwt as pyjwt
import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.application.services.authentication_service import AuthService
from src.common.infrastructure.adapters.security.token_blacklist import (
    RedisTokenBlacklistService,
)
from src.common.infrastructure.adapters.security.tokens import TokenService
from src.common.infrastructure.core import settings
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork
from src.common.utils.date_utils import get_current_datetime


@pytest.mark.asyncio
class TestAuthServiceBlacklist:
    async def _make_services(self):
        """Create fresh token + blacklist services with a clean Redis.

        Returns (token_service, blacklist_service, redis_client).
        The caller must ``await redis.aclose()`` after the test.
        """
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.flushdb()
        blacklist_service = RedisTokenBlacklistService(redis)
        token_service = TokenService(
            secret=settings.SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
        return token_service, blacklist_service, redis

    async def _make_uow(self) -> UnitOfWork:
        """Create a UoW from the app's session maker (patched to NullPool in conftest)."""
        session = AsyncSessionMaker()
        return UnitOfWork(session)

    async def test_valid_token_passes_blacklist_check(
        self,
        seed_session: AsyncSession,
        test_user_id: str,
    ):
        token_service, blacklist_service, redis = await self._make_services()
        try:
            token = token_service.generate({"user_id": test_user_id}, exp_minutes=60)
            auth_service = AuthService(
                token_service=token_service,
                blacklist_service=blacklist_service,
            )

            uow = await self._make_uow()
            async with uow:
                user = await auth_service.get_authenticated_user(uow=uow, token=token)

            assert user is not None
            assert str(user.id) == test_user_id
        finally:
            await redis.aclose()

    async def test_blacklisted_token_raises_unauthorized(
        self,
        seed_session: AsyncSession,
        test_user_id: str,
    ):
        token_service, blacklist_service, redis = await self._make_services()
        try:
            token = token_service.generate({"user_id": test_user_id}, exp_minutes=60)
            auth_service = AuthService(
                token_service=token_service,
                blacklist_service=blacklist_service,
            )

            # Extract jti for blacklisting
            payload = token_service.decode(token)
            await blacklist_service.blacklist(payload["jti"], ttl=120)

            from src.common.domain.exceptions import UnauthorizedError

            uow = await self._make_uow()
            async with uow:
                with pytest.raises(UnauthorizedError) as exc_info:
                    await auth_service.get_authenticated_user(uow=uow, token=token)

            assert "No autorizado" in str(exc_info.value)
        finally:
            await redis.aclose()

    async def test_token_without_jti_skips_blacklist_check(
        self,
        seed_session: AsyncSession,
        test_user_id: str,
    ):
        """Old tokens (before jti was added) still work — blacklist check
        is skipped when the claim is absent."""
        token_service, blacklist_service, redis = await self._make_services()
        try:
            auth_service = AuthService(
                token_service=token_service,
                blacklist_service=blacklist_service,
            )

            # Manually encode a token WITHOUT jti
            payload = {
                "user_id": test_user_id,
                "exp": get_current_datetime() + timedelta(minutes=60),
                "iat": get_current_datetime(),
            }
            token = pyjwt.encode(payload, settings.SECRET, settings.JWT_ALGORITHM)

            uow = await self._make_uow()
            async with uow:
                user = await auth_service.get_authenticated_user(uow=uow, token=token)

            assert user is not None
            assert str(user.id) == test_user_id
        finally:
            await redis.aclose()
