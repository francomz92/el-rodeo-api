"""Integration tests for the /auth/password-change endpoint.

The ChangePassword endpoint no longer accepts a `token` field in the body.
Authentication is via Authorization: Bearer header only (or cookie).
"""

from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.infrastructure.adapters.security.hashers import SecurityService
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.dependencies.redis import (
    _get_redis_client,
)


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
        name="Password Change Test User",
        dni=uid.hex[:8],
        email=f"pw-change-{uid.hex[:8]}@example.com",
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
async def auth_client(password_user: dict[str, Any]) -> AsyncClient:
    """Return an AsyncClient with a logged-in session (Bearer token in headers).

    Sets up clean Redis and logs in to obtain a real token.
    The client is ready to make authenticated requests.
    """
    # Clean Redis
    cleanup = Redis.from_url(settings.REDIS_URL)
    await cleanup.flushdb()
    await cleanup.aclose()

    async def _test_redis():
        redis = Redis.from_url(settings.REDIS_URL)
        try:
            yield redis
        finally:
            await redis.aclose()

    app.dependency_overrides[_get_redis_client] = _test_redis

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Login
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": password_user["dni"],
                    "password": password_user["password"],
                },
            )
            assert resp.status_code == 200, f"Login failed: {resp.text}"
            token = resp.json()["access_token"]
            ac.headers["Authorization"] = f"Bearer {token}"
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestChangePasswordAPI:
    """POST /auth/password-change — change password flow."""

    async def test_change_password_with_valid_auth_returns_200(self, password_user: dict[str, Any], auth_client: AsyncClient) -> None:
        """Authenticated user can change their password."""
        resp = await auth_client.post(
            "/auth/password-change",
            json={
                "password": password_user["password"],
                "new_password": "new-strong-password-456",
                "confirmed_password": "new-strong-password-456",
            },
        )
        assert resp.status_code == 200, f"Password change failed: {resp.text}"

    async def test_change_password_without_auth_returns_401(self, password_user: dict[str, Any]) -> None:
        """Missing Authorization header returns 401."""

        async def _test_redis():
            redis = Redis.from_url(settings.REDIS_URL)
            try:
                yield redis
            finally:
                await redis.aclose()

        app.dependency_overrides[_get_redis_client] = _test_redis

        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/auth/password-change",
                    json={
                        "password": "irrelevant",
                        "new_password": "new-strong-password-456",
                        "confirmed_password": "new-strong-password-456",
                    },
                    # No Authorization header
                )
                assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
        finally:
            app.dependency_overrides.clear()

    async def test_change_password_with_wrong_current_password(self, auth_client: AsyncClient) -> None:
        """Wrong current password returns a client error."""
        resp = await auth_client.post(
            "/auth/password-change",
            json={
                "password": "wrong-password-xxx",
                "new_password": "new-strong-password-456",
                "confirmed_password": "new-strong-password-456",
            },
        )
        # Implementation raises UnauthorizedError (401) for wrong password
        assert resp.status_code in (400, 401, 422), f"Expected 4xx, got {resp.status_code}: {resp.text}"
