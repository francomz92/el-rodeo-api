"""Test fixtures for observability integration tests.

Uses the main app from ``main`` like other integration tests.
For Prometheus tests, a module-level env var toggle is used.
"""

import os
from typing import Any, AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Rate limiting off for observability tests
os.environ.setdefault("ENABLE_RATE_LIMIT", "false")

from main import app  # noqa: E402


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, Any]:
    """Provide an HTTPX AsyncClient against the main app.

    This is the unauthenticated client — health and metrics endpoints
    do not require authentication.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
