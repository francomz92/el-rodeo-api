"""Integration tests for the /auth/refresh endpoint (refresh token rotation).

These tests use a *real* login flow to get tokens and then verify the
refresh cycle, token reuse detection, and error conditions.

Relies on the `password_user` fixture shared across auth integration tests
for seeding a user with known credentials.
"""

from typing import Any
from uuid import uuid4

import jwt as pyjwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.infrastructure.adapters.security.hashers import SecurityService
from src.common.infrastructure.core import settings as app_settings
from src.common.infrastructure.presentation.dependencies.redis import (
    _get_redis_client,
)


def _error_message(response_body: dict) -> str:
    """Extract error message from the standard error response format."""
    error = response_body.get("error", {})
    return error.get("message", "")


@pytest_asyncio.fixture(scope="function")
async def password_user(seed_session: AsyncSession) -> dict[str, Any]:
    """Seed a user with a known password and return credentials + id."""
    from src.auth.infrastructure.persistence.models._user_models import User

    uid = uuid4()
    plain_password = "test-password-123"
    hasher = SecurityService()
    hashed = await hasher.hash_password(plain_password)

    user = User(
        id=uid,
        name="Refresh Test User",
        dni=uid.hex[:8],
        email=f"refresh-{uid.hex[:8]}@example.com",
        password=hashed,
    )
    seed_session.add(user)
    await seed_session.commit()

    return {
        "user_id": str(uid),
        "dni": uid.hex[:8],
        "password": plain_password,
    }


@pytest_asyncio.fixture(scope="function")
async def token_pair(password_user: dict[str, Any]) -> dict[str, str]:
    """Log in and return the access + refresh token pair.

    Overrides Redis dependency for clean test isolation per test.
    """
    from redis.asyncio import Redis as _Redis

    _cleanup = _Redis.from_url(app_settings.REDIS_URL)
    await _cleanup.flushdb()
    await _cleanup.aclose()

    async def _test_redis():
        redis = Redis.from_url(app_settings.REDIS_URL)
        try:
            yield redis
        finally:
            await redis.aclose()

    app.dependency_overrides[_get_redis_client] = _test_redis

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": password_user["dni"],
                    "password": password_user["password"],
                },
            )
            assert resp.status_code == 200, f"Login failed: {resp.text}"
            body = resp.json()
            yield {
                "access_token": body["access_token"],
                "refresh_token": body["refresh_token"],
            }
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestRefreshTokenAPI:
    """POST /auth/refresh — refresh token rotation cycle."""

    async def _client(self):
        """Create a fresh test client with a clean Redis override."""

        async def _test_redis():
            redis = Redis.from_url(app_settings.REDIS_URL)
            try:
                yield redis
            finally:
                await redis.aclose()

        app.dependency_overrides[_get_redis_client] = _test_redis
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    async def test_full_refresh_cycle(self, token_pair: dict[str, str]) -> None:
        """Login → refresh → old token rejected (rotation)."""
        refresh_token = token_pair["refresh_token"]
        ac = await self._client()
        try:
            # Act: refresh with the valid token
            resp = await ac.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert resp.status_code == 200, f"Refresh failed: {resp.text}"
            body = resp.json()
            assert "access_token" in body
            assert "refresh_token" in body
            new_refresh = body["refresh_token"]
            assert new_refresh != refresh_token, "Refresh token was NOT rotated"

            # Assert: old token is now invalid (reuse detection)
            resp2 = await ac.post(
                "/auth/refresh",
                json={"refresh_token": refresh_token},
            )
            assert resp2.status_code == 401, f"Old token should be revoked, got {resp2.status_code}: {resp2.text}"
            msg = _error_message(resp2.json())
            assert "token_family_revoked" in msg, f"Unexpected error: {msg}"
        finally:
            await ac.aclose()
            app.dependency_overrides.clear()

    async def test_refresh_with_valid_token_returns_200(self, token_pair: dict[str, str]) -> None:
        """A valid refresh token returns 200 with new tokens."""
        ac = await self._client()
        try:
            resp = await ac.post(
                "/auth/refresh",
                json={"refresh_token": token_pair["refresh_token"]},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "access_token" in body
            assert "refresh_token" in body
            assert len(body["access_token"]) > 0
            assert len(body["refresh_token"]) > 0
        finally:
            await ac.aclose()
            app.dependency_overrides.clear()

    async def test_refresh_with_expired_token_returns_401(self) -> None:
        """An expired refresh token returns 401."""
        ac = await self._client()
        try:
            expired_token = pyjwt.encode(
                {
                    "user_id": "00000000-0000-0000-0000-000000000000",
                    "type": "refresh",
                    "exp": 1000000000,  # expired in 2001
                    "iat": 1000000000,
                    "jti": "00000000-0000-0000-0000-000000000000",
                    "refresh_token_id": "00000000-0000-0000-0000-000000000000",
                    "family_id": "00000000-0000-0000-0000-000000000000",
                },
                app_settings.SECRET,
                app_settings.JWT_ALGORITHM,
            )

            resp = await ac.post(
                "/auth/refresh",
                json={"refresh_token": expired_token},
            )
            assert resp.status_code == 401
            msg = _error_message(resp.json())
            assert "expired" in msg.lower(), f"Unexpected error: {msg}"
        finally:
            await ac.aclose()
            app.dependency_overrides.clear()

    async def test_refresh_with_invalid_token_returns_401(self) -> None:
        """A completely bogus refresh token returns 401."""
        ac = await self._client()
        try:
            resp = await ac.post(
                "/auth/refresh",
                json={"refresh_token": "this.is.not.a.valid.jwt"},
            )
            assert resp.status_code == 401
        finally:
            await ac.aclose()
            app.dependency_overrides.clear()
