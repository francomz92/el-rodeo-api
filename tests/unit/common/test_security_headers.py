"""Unit tests for SecurityHeadersMiddleware.

Verifies that the ASGI middleware injects the correct security headers
on every response and omits HSTS in development mode.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest

from src.common.infrastructure.presentation.middlewares.security_headers import (
    SecurityHeadersMiddleware,
)


def _make_asgi_app() -> Any:
    """Build a minimal ASGI app that sends a response start message."""

    async def app(scope: Any, receive: Any, send: Any) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{"ok": true}',
            }
        )

    return app


@pytest.fixture
def dev_settings() -> MagicMock:
    settings = MagicMock()
    settings.ENVIRONMENT = "development"
    settings.CSP_DEFAULT_SRC = "'self'"
    settings.CSP_DIRECTIVES = None
    settings.HSTS_MAX_AGE = 31536000
    settings.DEBUG = True
    return settings


@pytest.fixture
def prod_settings() -> MagicMock:
    settings = MagicMock()
    settings.ENVIRONMENT = "production"
    settings.CSP_DEFAULT_SRC = "'self'"
    settings.CSP_DIRECTIVES = None
    settings.HSTS_MAX_AGE = 31536000
    settings.DEBUG = False
    return settings


@pytest.fixture
def csp_directives_settings() -> MagicMock:
    settings = MagicMock()
    settings.ENVIRONMENT = "production"
    settings.CSP_DEFAULT_SRC = "'self'"
    settings.CSP_DIRECTIVES = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self' data:",
        "connect-src": "'self'",
        "base-uri": "'self'",
        "form-action": "'self'",
    }
    settings.HSTS_MAX_AGE = 31536000
    settings.DEBUG = False
    return settings


class TestSecurityHeadersMiddleware:
    """SecurityHeadersMiddleware must inject security headers on every response."""

    @staticmethod
    async def _run_scenario(
        settings: Any,
        scope: dict | None = None,
    ) -> list[tuple[bytes, bytes]]:
        """Execute middleware and return the response headers."""
        headers: list[tuple[bytes, bytes]] = []
        app = _make_asgi_app()
        middleware = SecurityHeadersMiddleware(app, settings)
        actual_scope = scope or {"type": "http", "method": "GET", "path": "/api/test"}

        async def noop_receive() -> dict:
            return {"type": "http.request"}

        async def capture_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers.extend(message.get("headers", []))

        await middleware(actual_scope, noop_receive, capture_send)
        return headers

    async def test_sets_x_content_type_options(self, prod_settings) -> None:
        """X-Content-Type-Options: nosniff is set on all responses."""
        headers = await self._run_scenario(prod_settings)
        assert (b"x-content-type-options", b"nosniff") in headers

    async def test_sets_x_frame_options(self, prod_settings) -> None:
        """X-Frame-Options: DENY is set on all responses."""
        headers = await self._run_scenario(prod_settings)
        assert (b"x-frame-options", b"DENY") in headers

    async def test_sets_csp(self, prod_settings) -> None:
        """Content-Security-Policy is set on all responses."""
        headers = await self._run_scenario(prod_settings)
        assert (b"content-security-policy", b"default-src 'self'") in headers

    async def test_sets_referrer_policy(self, prod_settings) -> None:
        """Referrer-Policy is set on all responses."""
        headers = await self._run_scenario(prod_settings)
        assert (b"referrer-policy", b"strict-origin-when-cross-origin") in headers

    async def test_sets_permissions_policy(self, prod_settings) -> None:
        """Permissions-Policy is set on all responses."""
        headers = await self._run_scenario(prod_settings)
        assert (b"permissions-policy", b"geolocation=(), microphone=(), camera=()") in headers

    async def test_sets_hsts_in_production(self, prod_settings) -> None:
        """Strict-Transport-Security is set in production."""
        headers = await self._run_scenario(prod_settings)
        assert (b"strict-transport-security", b"max-age=31536000; includeSubDomains") in headers

    async def test_omits_hsts_in_development(self, dev_settings) -> None:
        """Strict-Transport-Security is NOT set in development."""
        headers = await self._run_scenario(dev_settings)
        hsts_headers = [h for h in headers if h[0] == b"strict-transport-security"]
        assert len(hsts_headers) == 0

    async def test_csp_expanded_with_directives(self, csp_directives_settings) -> None:
        """CSP header includes all directives when CSP_DIRECTIVES is set."""
        headers = await self._run_scenario(csp_directives_settings)
        csp_headers = [h for h in headers if h[0] == b"content-security-policy"]
        assert len(csp_headers) == 1
        csp_value = csp_headers[0][1].decode()

        assert "default-src 'self'" in csp_value
        assert "script-src 'self'" in csp_value
        assert "style-src 'self'" in csp_value
        assert "img-src 'self' data:" in csp_value
        assert "connect-src 'self'" in csp_value
        assert "base-uri 'self'" in csp_value
        assert "form-action 'self'" in csp_value

    async def test_csp_falls_back_to_default_src(self, prod_settings) -> None:
        """CSP falls back to CSP_DEFAULT_SRC when CSP_DIRECTIVES is not set."""
        headers = await self._run_scenario(prod_settings)
        assert (b"content-security-policy", b"default-src 'self'") in headers

    async def test_unknown_scope_passes_through(self, prod_settings) -> None:
        """Non-HTTP scopes (e.g. websocket) pass through without headers."""
        inner_called = False
        received_scope: Any = None

        async def passthrough_app(scope: Any, receive: Any, send: Any) -> None:
            nonlocal inner_called, received_scope
            inner_called = True
            received_scope = scope

        middleware = SecurityHeadersMiddleware(passthrough_app, prod_settings)
        scope = {"type": "websocket", "path": "/ws"}

        async def noop_receive() -> dict:
            return {"type": "websocket.receive"}

        async def noop_send(message: dict) -> None:
            pass

        await middleware(scope, noop_receive, noop_send)

        assert inner_called, "Inner app must be called"
        assert received_scope == scope, "Scope must be passed through unchanged"
