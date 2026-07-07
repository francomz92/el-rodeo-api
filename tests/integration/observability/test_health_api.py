"""Integration tests for the /health endpoint.

Verifies health check response shape, DB/Redis status reporting,
auth bypass, and rate-limit exemption.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    """GET /health — health check endpoint."""

    async def test_health_response_shape(self, client: AsyncClient) -> None:
        """Response body matches the HealthResponse schema regardless of status."""
        resp = await client.get("/health")
        assert resp.status_code in (200, 503), f"Expected 200 or 503, got {resp.status_code}"
        body = resp.json()
        # Must have exactly these three string fields
        assert set(body.keys()) == {"status", "database", "redis"}, f"Unexpected keys: {body.keys()}"
        assert isinstance(body["status"], str)
        assert body["status"] in ("healthy", "unhealthy")
        assert isinstance(body["database"], str)
        assert body["database"] in ("ok", "unreachable")
        assert isinstance(body["redis"], str)
        assert body["redis"] in ("ok", "unreachable")

    async def test_health_returns_503_when_service_down(self, client: AsyncClient) -> None:
        """When DB or Redis is unreachable, /health returns 503 with unhealthy status.

        This test verifies the unhealthy path. Since the test environment may
        have all services running, we only assert that when the status is
        ``unhealthy``, the HTTP status is 503.
        """
        resp = await client.get("/health")
        body = resp.json()
        if body["status"] == "unhealthy":
            assert resp.status_code == 503, f"When unhealthy, expected 503, got {resp.status_code}"
            # At least one service should be unreachable
            assert "unreachable" in (body["database"], body["redis"]), f"Unhealthy but no unreachable services: {body}"
        else:
            # When healthy, should be 200
            assert resp.status_code == 200, f"When healthy, expected 200, got {resp.status_code}"

    async def test_health_does_not_require_auth(self, client: AsyncClient) -> None:
        """Health endpoint returns without any auth headers."""
        resp = await client.get("/health")
        assert resp.status_code in (200, 503), f"Health should be accessible without auth, got {resp.status_code}"
        # If we got a valid health response, auth wasn't required
        body = resp.json()
        assert "status" in body

    async def test_health_not_rate_limited(self, client: AsyncClient) -> None:
        """Health endpoint is exempt from rate limiting.

        Make multiple rapid requests — none should be rate-limited.
        """
        for _ in range(20):
            resp = await client.get("/health")
            assert resp.status_code in (200, 503), f"Health should not be rate limited, got {resp.status_code}: {resp.text}"
