"""Integration tests for the /auth/login cookie-based authentication.

Tests the dual-mode login behavior:
- Web clients (X-Requested-With: XMLHttpRequest) get HttpOnly cookies
- Mobile/3rd-party clients get Bearer tokens in body only
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
    """Seed a user with a known password."""
    from src.auth.infrastructure.persistence.models._user_models import User

    uid = uuid4()
    plain_password = "test-password-123"
    hasher = SecurityService()
    hashed = await hasher.hash_password(plain_password)

    user = User(
        id=uid,
        name="Login Cookie Test User",
        dni=uid.hex[:8],
        email=f"login-cookie-{uid.hex[:8]}@example.com",
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
async def clean_redis() -> None:
    """Flush Redis and override the Redis dependency for test isolation.

    Applied as an autouse-style fixture per test.
    """
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
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestLoginCookieAPI:
    """POST /auth/login — cookie-based web login flow."""

    async def test_login_sets_cookie_for_xhr(self, password_user: dict[str, Any], clean_redis: None) -> None:
        """Login with X-Requested-With: XMLHttpRequest sets Set-Cookie headers."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": password_user["dni"],
                    "password": password_user["password"],
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            assert resp.status_code == 200, f"Login failed: {resp.text}"

            set_cookie = resp.headers.get("set-cookie", "")
            assert "access_token" in set_cookie, f"access_token cookie not set. Headers: {dict(resp.headers)}"
            assert "refresh_token" in set_cookie, f"refresh_token cookie not set. Headers: {dict(resp.headers)}"
            assert "HttpOnly" in set_cookie
            assert "Max-Age=900" in set_cookie or "max-age=900" in set_cookie.lower()
            assert "SameSite=strict" in set_cookie.lower() or "samesite=strict" in set_cookie.lower()

    async def test_login_returns_json_with_tokens(self, password_user: dict[str, Any], clean_redis: None) -> None:
        """Login returns JSON body with access_token and refresh_token."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": password_user["dni"],
                    "password": password_user["password"],
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            assert resp.status_code == 200
            body = resp.json()
            assert "access_token" in body
            assert "refresh_token" in body
            assert len(body["access_token"]) > 0
            assert len(body["refresh_token"]) > 0

    async def test_login_without_xhr_no_cookies(self, password_user: dict[str, Any], clean_redis: None) -> None:
        """Login without X-Requested-With header does NOT set cookies (Bearer-only mode)."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/auth/login",
                json={
                    "dni": password_user["dni"],
                    "password": password_user["password"],
                },
                # No X-Requested-With header
            )
            assert resp.status_code == 200

            # Cookies should NOT be set
            set_cookie = resp.headers.get("set-cookie", "")
            assert "access_token" not in set_cookie, "access_token cookie should NOT be present without X-Requested-With"

            # Body should still have tokens
            body = resp.json()
            assert "access_token" in body
            assert "refresh_token" in body
