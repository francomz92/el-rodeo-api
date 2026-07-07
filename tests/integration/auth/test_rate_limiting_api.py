"""Integration tests for HTTP rate limiting via slowapi middleware.

Tests that endpoints return 429 when rate limits are exceeded and that
the Retry-After header is present.

Uses a minimal FastAPI test app with rate limiting enabled and a low
limit so the test runs quickly.
"""

import pytest
import pytest_asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.common.infrastructure.presentation.middlewares.ip_utils import get_client_ip


@pytest_asyncio.fixture(scope="function")
async def rate_limited_app() -> FastAPI:
    """Create a minimal FastAPI app with a 3/minute rate limit on a test route."""
    app = FastAPI()
    limiter = Limiter(
        key_func=get_client_ip,
        storage_uri="memory://",
        default_limits=[],
    )

    @app.get("/test-rate-limit")
    @limiter.limit("3/minute")
    async def test_endpoint(request: Request):
        return {"ok": True}

    @app.get("/unlimited")
    async def unlimited_endpoint():
        return {"ok": True}

    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
            headers={"Retry-After": "60"},
        )

    app.state.limiter = limiter
    app.add_exception_handler(429, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    return app


@pytest.mark.asyncio
class TestRateLimitingAPI:
    """Rate limiting via slowapi middleware."""

    async def test_exceeding_rate_limit_returns_429(self, rate_limited_app: FastAPI) -> None:
        """More requests than the limit within the window return 429."""
        transport = ASGITransport(app=rate_limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # First 3 requests should succeed (limit is 3/minute)
            for i in range(3):
                resp = await ac.get("/test-rate-limit")
                assert resp.status_code == 200, f"Request {i + 1} should succeed, got {resp.status_code}"

            # 4th request should be rate limited
            resp = await ac.get("/test-rate-limit")
            assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"

    async def test_retry_after_header_present(self, rate_limited_app: FastAPI) -> None:
        """Rate limited responses include the Retry-After header."""
        transport = ASGITransport(app=rate_limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Exhaust the limit
            for _ in range(3):
                await ac.get("/test-rate-limit")

            # 4th request gets 429 with Retry-After
            resp = await ac.get("/test-rate-limit")
            assert resp.status_code == 429
            retry_after = resp.headers.get("retry-after", "")
            assert retry_after, "Retry-After header is missing"
            # Retry-After should be a positive integer (seconds)
            assert retry_after.isdigit(), f"Retry-After should be a number, got '{retry_after}'"
            assert int(retry_after) > 0

    async def test_unlimited_endpoint_not_affected(self, rate_limited_app: FastAPI) -> None:
        """Endpoints without rate limits are not affected by other limits."""
        transport = ASGITransport(app=rate_limited_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # Make 10 requests to the unlimited endpoint
            for i in range(10):
                resp = await ac.get("/unlimited")
                assert resp.status_code == 200, f"Unlimited request {i + 1} should succeed, got {resp.status_code}"
