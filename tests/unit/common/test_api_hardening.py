"""Unit tests for Phase 8 — API Hardening middleware.

Covers:
- BodySizeLimitMiddleware returns 413 for oversized requests
- CorrelationIdMiddleware sanitizes malicious X-Request-ID values
- server_exception_handler returns generic message without leaking exc info
"""

import re
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.common.infrastructure.presentation.middlewares.body_size_limit import (
    BodySizeLimitMiddleware,
)
from src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error import (
    server_exception_handler,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_cid_context() -> Any:
    """Clear correlation ID context between tests."""
    from src.common.infrastructure.adapters.correlation import correlation_id_var

    correlation_id_var.set("")
    yield


def _make_asgi_app() -> Any:
    """Build a minimal ASGI app that sends a success response."""

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


def _make_scope(
    *,
    method: str = "POST",
    path: str = "/api/test",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> dict:
    """Build a minimal HTTP scope dict."""
    return {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": headers or [],
        "client": ("127.0.0.1", 54321),
        "server": ("localhost", 8000),
        "scheme": "http",
    }


# ── BodySizeLimitMiddleware tests ──────────────────────────────────────────────


class TestBodySizeLimitMiddleware:
    """BodySizeLimitMiddleware must reject oversized payloads with 413."""

    @staticmethod
    async def _run(
        content_length: int | None = None,
        max_size: int = 10_485_760,
    ) -> tuple[int, dict]:
        """Execute middleware and return (status_code, body_dict)."""
        headers = []
        if content_length is not None:
            headers.append((b"content-length", str(content_length).encode()))

        scope = _make_scope(headers=headers)
        app = _make_asgi_app()
        middleware = BodySizeLimitMiddleware(app, max_size=max_size)

        status: list[int] = [0]
        body_parts: list[bytes] = []

        async def noop_receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def capture_send(message: dict) -> None:
            if message["type"] == "http.response.start":
                status[0] = message["status"]
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        await middleware(scope, noop_receive, capture_send)
        body = b"".join(body_parts)
        import json

        return status[0], json.loads(body) if body else {}

    async def test_passes_through_small_request(self) -> None:
        """Requests under the limit pass through to the inner app."""
        status, body = await self._run(content_length=1024)
        assert status == 200
        assert body == {"ok": True}

    async def test_rejects_oversized_request(self) -> None:
        """Requests exceeding the limit receive a 413 response."""
        max_size = 1024
        status, body = await self._run(content_length=2048, max_size=max_size)
        assert status == 413
        assert body.get("success") is False
        assert body.get("error", {}).get("code") == "request_entity_too_large"

    async def test_rejects_exactly_over_limit(self) -> None:
        """Request at limit+1 byte is rejected."""
        max_size = 100
        status, body = await self._run(content_length=101, max_size=max_size)
        assert status == 413

    async def test_allows_at_limit(self) -> None:
        """Request exactly at the limit is allowed through."""
        max_size = 1024
        status, body = await self._run(content_length=1024, max_size=max_size)
        assert status == 200

    async def test_no_content_length_passes_through(self) -> None:
        """Requests without Content-Length header pass through."""
        status, body = await self._run(content_length=None)
        assert status == 200

    async def test_passes_through_non_http_scope(self) -> None:
        """Non-HTTP scopes (e.g. websocket) pass through."""
        inner_called = False

        async def passthrough_app(scope: Any, receive: Any, send: Any) -> None:
            nonlocal inner_called
            inner_called = True

        middleware = BodySizeLimitMiddleware(passthrough_app)
        scope = {"type": "websocket", "path": "/ws"}

        async def noop_receive() -> dict:
            return {"type": "websocket.receive"}

        async def noop_send(message: dict) -> None:
            pass

        await middleware(scope, noop_receive, noop_send)
        assert inner_called


# ── CorrelationIdMiddleware sanitization tests ─────────────────────────────────


class TestCorrelationIdSanitization:
    """CorrelationIdMiddleware must validate and sanitize X-Request-ID."""

    @staticmethod
    async def _run_with_header(header_value: str | None) -> str:
        """Execute CorrelationIdMiddleware and return the CID it set."""
        from src.common.infrastructure.adapters.correlation import (
            get_correlation_id,
        )
        from src.common.infrastructure.presentation.middlewares.correlation_id import (
            CorrelationIdMiddleware,
        )

        headers = []
        if header_value is not None:
            headers.append((b"x-request-id", header_value.encode()))

        scope = _make_scope(headers=headers)

        async def passthrough_app(scope: Any, receive: Any, send: Any) -> None:
            async def send_wrapper(message: dict) -> None:
                pass

            await send(scope)

        middleware = CorrelationIdMiddleware(passthrough_app)

        async def noop_receive() -> dict:
            return {"type": "http.request"}

        async def capture_send(message: dict) -> None:
            pass

        await middleware(scope, noop_receive, capture_send)
        return get_correlation_id()

    async def test_valid_cid_is_reflected(self) -> None:
        """A valid X-Request-ID is reflected back."""
        cid = await self._run_with_header("abc-123-def")
        assert cid == "abc-123-def"

    async def test_too_long_cid_generates_new(self) -> None:
        """X-Request-ID over 64 chars generates a new UUID instead."""
        too_long = "a" * 65
        cid = await self._run_with_header(too_long)
        assert len(cid) == 32  # UUID hex
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_special_chars_generates_new(self) -> None:
        """X-Request-ID with special characters generates a new UUID."""
        cid = await self._run_with_header("abc<script>alert(1)</script>")
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_spaces_generates_new(self) -> None:
        """X-Request-ID with spaces generates a new UUID."""
        cid = await self._run_with_header("abc def ghi")
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_empty_header_generates_new(self) -> None:
        """Missing X-Request-ID header generates a new UUID."""
        cid = await self._run_with_header(None)
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_alphanumeric_only_is_valid(self) -> None:
        """Alphanumeric only (no hyphens) is valid."""
        cid = await self._run_with_header("a1b2c3d4e5f6g7h8i9j0")
        assert cid == "a1b2c3d4e5f6g7h8i9j0"

    async def test_hyphens_are_valid(self) -> None:
        """Hyphens in X-Request-ID are valid."""
        cid = await self._run_with_header("req-123-abc-456")
        assert cid == "req-123-abc-456"

    async def test_whitespace_only_stripped_and_then_invalid(self) -> None:
        """X-Request-ID with only whitespace is treated as invalid."""
        cid = await self._run_with_header("   ")
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)

    async def test_empty_string_generates_new(self) -> None:
        """Empty X-Request-ID generates a new UUID."""
        cid = await self._run_with_header("")
        assert len(cid) == 32
        assert re.fullmatch(r"[0-9a-f]{32}", cid)


# ── server_exception_handler tests ─────────────────────────────────────────────


class TestServerExceptionHandler:
    """server_exception_handler must return generic message without leaking exc info."""

    async def test_returns_generic_error_message(self) -> None:
        """The error message is generic, not the exception text."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"

        response = await server_exception_handler(
            request,
            Exception("This is a SECRET database error"),
        )

        body = response.body.decode()
        assert "SECRET database error" not in body
        assert "Error interno del servidor" in body

    async def test_returns_server_error_code(self) -> None:
        """The error code is 'server_error'."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"

        response = await server_exception_handler(
            request,
            Exception("some error"),
        )

        body = response.body.decode()
        assert "server_error" in body

    async def test_returns_500_status(self) -> None:
        """The response status is 500."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"

        response = await server_exception_handler(
            request,
            Exception("some error"),
        )

        assert response.status_code == 500

    async def test_uses_log_exception(self) -> None:
        """log.exception() is called (not log.error)."""
        from fastapi import Request

        request = MagicMock(spec=Request)
        request.url.path = "/api/test"

        with patch("src.common.infrastructure.presentation.middlewares.exceptions_handlers.server_error.log") as mock_log:
            await server_exception_handler(
                request,
                Exception("some error"),
            )
            # log.exception should have been called (one of the calls)
            assert mock_log.exception.called
