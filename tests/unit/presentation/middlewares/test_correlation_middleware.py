"""Unit tests for the Correlation ID ASGI middleware.

Tests that the middleware correctly propagates client-provided correlation
IDs, generates UUIDs when none are provided, echoes the ID in response
headers, and makes the ID available via get_correlation_id() in handlers.
"""

import re

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def correlation_app():
    """Create a minimal FastAPI app with the correlation middleware.

    NOTE: Uses an inline import of ``get_correlation_id`` rather than a
    module-level import because ``test_db.py:_fresh_db_module`` clears ALL
    ``src.*`` modules from ``sys.modules`` during the test run.  If a
    module-level import binds ``get_correlation_id`` from copy A of the
    ``correlation`` module, but the middleware (imported later, inline)
    picks up copy B, the handler reads a **different** ``ContextVar`` than
    the middleware writes to.
    """
    from src.common.infrastructure.adapters.correlation import get_correlation_id

    app = FastAPI()

    @app.get("/test")
    async def test_endpoint():
        return {"correlation_id": get_correlation_id()}

    @app.get("/echo-headers")
    async def echo_headers(request):
        return {"x-request-id": request.headers.get("x-request-id", "")}

    return app


class TestCorrelationIdMiddleware:
    """Correlation ID ASGI middleware behavior."""

    async def test_propagates_client_provided_id(self, correlation_app):
        """When X-Request-ID header is sent, that value is used as the correlation ID."""
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        correlation_app.add_middleware(CorrelationIdMiddleware)
        transport = ASGITransport(app=correlation_app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/test", headers={"X-Request-ID": "abc-123"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["correlation_id"] == "abc-123"

    async def test_generates_uuid_when_no_header(self, correlation_app):
        """When no X-Request-ID header is present, a UUID hex is generated."""
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        correlation_app.add_middleware(CorrelationIdMiddleware)
        transport = ASGITransport(app=correlation_app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/test")

        assert resp.status_code == 200
        data = resp.json()
        cid = data["correlation_id"]
        assert isinstance(cid, str)
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_response_includes_x_request_id_header(self, correlation_app):
        """The response includes an X-Request-ID header with the correlation ID."""
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        correlation_app.add_middleware(CorrelationIdMiddleware)
        transport = ASGITransport(app=correlation_app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/test", headers={"X-Request-ID": "my-custom-id"})

        assert resp.status_code == 200
        assert resp.headers.get("x-request-id") == "my-custom-id"

    async def test_response_includes_generated_id(self, correlation_app):
        """When no header is sent, the response X-Request-ID has the generated UUID."""
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        correlation_app.add_middleware(CorrelationIdMiddleware)
        transport = ASGITransport(app=correlation_app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/test")

        assert resp.status_code == 200
        resp_cid = resp.headers.get("x-request-id", "")
        assert len(resp_cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", resp_cid)

    async def test_correlation_id_available_in_handler(self, correlation_app):
        """The handler can retrieve the correlation ID via get_correlation_id().

        This tests that the middleware sets the contextvar BEFORE the handler runs.
        """
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        correlation_app.add_middleware(CorrelationIdMiddleware)

        @correlation_app.get("/check-ctxvar")
        async def check_ctxvar():
            from src.common.infrastructure.adapters.correlation import get_correlation_id

            return {"ctx_cid": get_correlation_id()}

        transport = ASGITransport(app=correlation_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/check-ctxvar", headers={"X-Request-ID": "handler-test"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["ctx_cid"] == "handler-test"

    async def test_non_http_scope_passed_through(self):
        """Non-HTTP scopes (e.g. websocket) are passed through without modification."""
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        # Create a mock ASGI app that records it was called
        was_called = False

        async def mock_app(scope, receive, send):
            nonlocal was_called
            was_called = True

        middleware = CorrelationIdMiddleware(mock_app)
        await middleware({"type": "websocket"}, None, None)

        assert was_called, "Non-HTTP scope should be forwarded directly"
