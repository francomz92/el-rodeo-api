"""Integration tests for the logout API endpoint.

These tests use a *real* login flow to get a token and then verify that
logging out invalidates it. The auth override used by other integration
tests is NOT applied here — we need the actual auth chain to be active.

Each test creates its own Redis connection to avoid event-loop conflicts.
"""

from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.infrastructure.adapters.security.hashers import SecurityService
from src.common.infrastructure.core import settings


@pytest_asyncio.fixture(scope="function")
async def password_user(seed_session: AsyncSession) -> dict[str, Any]:
    """Seed a user with a known password and return credentials + id."""
    from src.auth.infrastructure.persistence.models._user_models import User

    uid = uuid4()
    plain_password = "test-password-123"
    hasher = SecurityService()
    hashed = hasher.hash_password(plain_password)

    user = User(
        id=uid,
        name="Password Test User",
        dni=uid.hex[:8],
        email=f"pw-{uid.hex[:8]}@example.com",
        password=hashed,
        is_admin=False,
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
    """Client that logs in first, then provides the token as Bearer.

    Does NOT override auth dependencies — uses the real auth flow.
    Overrides the Redis dependency to use a fresh per-test connection.
    """
    from main import app

    # ── Start with a clean Redis test database ────────────────────────
    # Flush once, outside the request-scoped generator, so blacklist
    # entries persist across requests within the same test.
    from redis.asyncio import (
        Redis,
        Redis as _Redis,
    )

    from src.common.infrastructure.presentation.dependencies.redis import (
        _get_redis_client,
    )

    _cleanup_redis = _Redis.from_url(settings.REDIS_URL)
    await _cleanup_redis.flushdb()
    await _cleanup_redis.aclose()

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
class TestLogoutAPI:
    async def test_logout_invalidates_token(self, auth_client: AsyncClient):
        """After logout, the same token returns 401 on protected endpoints."""
        # Act: logout
        resp = await auth_client.post("/auth/logout")
        assert resp.status_code == 200, f"Logout failed: {resp.text}"
        assert resp.json()["message"] == "Sesión cerrada exitosamente"

        # Assert: token is now invalid — try a second logout (needs valid token)
        resp = await auth_client.post("/auth/logout")
        assert resp.status_code == 200, f"Second logout failed: {resp.text}"

        # Also verify a protected endpoint rejects the blacklisted token
        resp = await auth_client.get("/cattle/animals/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    async def test_double_logout_returns_200(self, auth_client: AsyncClient):
        """Logging out twice should still return 200 (idempotent)."""
        resp1 = await auth_client.post("/auth/logout")
        assert resp1.status_code == 200

        resp2 = await auth_client.post("/auth/logout")
        assert resp2.status_code == 200

    async def test_logout_with_valid_token(self, auth_client: AsyncClient):
        """Logout of a valid token succeeds."""
        resp = await auth_client.post("/auth/logout")
        assert resp.status_code == 200

    async def test_protected_endpoint_without_token(self, password_user):
        """Calling a protected endpoint without a token returns 401."""
        from main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/cattle/animals/00000000-0000-0000-0000-000000000000")
            assert resp.status_code == 401
