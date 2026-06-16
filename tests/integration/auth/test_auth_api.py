"""Integration tests for the /auth API endpoints.

Since auth routes use _get_current_user dependency overrides for protected
routes (register), we need to handle auth differently:
  - /auth/register requires admin (is_admin_user dependency)
  - /auth/login is public
  - /auth/password-change requires a valid token in the body
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestLoginIntegration:
    """POST /auth/login — authenticate a user."""

    async def test_login_returns_200(self, client: AsyncClient, test_user_id: str) -> None:
        """A valid login attempt returns 200 with an access token."""
        dni = test_user_id[:8]  # matches the fixture logic in conftest
        response = await client.post(
            "/auth/login",
            json={"dni": dni, "password": "any_password"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body

    async def test_login_returns_422_on_empty_payload(self, client: AsyncClient) -> None:
        """Missing fields return 422."""
        response = await client.post("/auth/login", json={})
        assert response.status_code == 422

    async def test_login_returns_422_on_short_password(self, client: AsyncClient) -> None:
        """Password shorter than 8 chars returns 422."""
        response = await client.post(
            "/auth/login",
            json={"dni": "12345678", "password": "short"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestRegisterIntegration:
    """POST /auth/register — create a new user (admin only)."""

    async def test_register_returns_422_on_empty_payload(self, client: AsyncClient) -> None:
        """Missing fields return 422."""
        response = await client.post("/auth/register", json={})
        assert response.status_code in (422,)

    async def test_register_returns_422_on_missing_required_fields(self, client: AsyncClient) -> None:
        """Missing name, dni, or email returns 422."""
        response = await client.post(
            "/auth/register",
            json={"name": "Solo nombre"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestChangePasswordIntegration:
    """POST /auth/password-change — change a user's password."""

    async def test_change_password_returns_422_on_empty_payload(
        self,
        client: AsyncClient,
    ) -> None:
        """Missing fields return 422."""
        response = await client.post("/auth/password-change", json={})
        assert response.status_code == 422

    async def test_change_password_returns_422_on_short_passwords(
        self,
        client: AsyncClient,
    ) -> None:
        """Passwords shorter than 8 chars return 422."""
        response = await client.post(
            "/auth/password-change",
            json={
                "token": "some-token",
                "password": "short",
                "new_password": "also_short",
                "confirmed_password": "also_short",
            },
        )
        assert response.status_code == 422
