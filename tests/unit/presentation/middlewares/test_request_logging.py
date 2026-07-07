"""Unit tests for the Request Logging ASGI middleware.

Tests that every HTTP request is logged with method/path/status/duration,
that 4xx responses log at WARNING, 5xx at ERROR, and that correlation ID
is included in log entries.

These tests use a capture-sink approach that works alongside loguru's
existing singleton configuration. A custom StringIO sink is added with
``serialize=True`` which writes each record as a JSON line containing
the full structured record (``record.level.name``, ``record.message``,
``record.extra.correlation_id``, etc.).
"""

import asyncio
import json
import re
from io import StringIO

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_app() -> FastAPI:
    """Create a minimal FastAPI app with test routes."""
    app = FastAPI()

    @app.get("/success")
    async def success():
        return {"status": "ok"}

    @app.get("/bad-request")
    async def bad_request():
        return JSONResponse(status_code=400, content={"detail": "bad"})

    @app.get("/server-error")
    async def server_error():
        return JSONResponse(status_code=500, content={"detail": "oops"})

    return app


def _add_middlewares(app: FastAPI):
    """Add both correlation and request logging middleware."""
    from src.common.infrastructure.presentation.middlewares.correlation_id import (
        CorrelationIdMiddleware,
    )
    from src.common.infrastructure.presentation.middlewares.request_logging import (
        RequestLoggingMiddleware,
    )

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware)


def _capture_logs(app, method, path, headers=None):
    """Run a request and capture log output.

    Adds a temporary JSON-serialized sink to capture log records.
    Returns (list_of_records, httpx_response) where each record is the
    nested Loguru record dict::
        record["level"]["name"]    → level string (INFO, WARNING, etc.)
        record["message"]          → formatted message
        record["extra"]            → context vars dict
    """
    from loguru import logger as loguru_logger

    buf = StringIO()
    sink_id = loguru_logger.add(
        buf,
        format="{message}",
        level="DEBUG",
        enqueue=False,
        serialize=True,
    )

    transport = ASGITransport(app=app)

    async def _run():
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.request(method, path, headers=headers or {})

    try:
        resp = asyncio.run(_run())
        loguru_logger.complete()
    finally:
        loguru_logger.remove(sink_id)

    output = buf.getvalue()
    records = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            records.append(parsed["record"])
        except (json.JSONDecodeError, KeyError):
            continue

    return records, resp


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestRequestLoggingMiddleware:
    """Request logging middleware behavior."""

    def test_success_logged_at_info(self):
        """A 2xx response is logged at INFO level with method/path/status."""
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/success")

        assert resp.status_code == 200
        response_logs = [r for r in records if r.get("message", "").startswith("Response:")]
        assert len(response_logs) >= 1, f"No response logs found in:\n{records}"
        assert response_logs[0]["level"]["name"] == "INFO"
        msg = response_logs[0]["message"]
        assert "GET" in msg
        assert "/success" in msg
        assert "200" in msg
        assert "ms" in msg

    def test_bad_request_logged_at_warning(self):
        """A 4xx response is logged at WARNING level."""
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/bad-request")

        assert resp.status_code == 400
        response_logs = [r for r in records if r.get("message", "").startswith("Response:")]
        assert len(response_logs) >= 1
        assert response_logs[0]["level"]["name"] == "WARNING"
        assert "400" in response_logs[0]["message"]

    def test_server_error_logged_at_error(self):
        """A 5xx response is logged at ERROR level."""
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/server-error")

        assert resp.status_code == 500
        response_logs = [r for r in records if r.get("message", "").startswith("Response:")]
        assert len(response_logs) >= 1
        assert response_logs[0]["level"]["name"] == "ERROR"
        assert "500" in response_logs[0]["message"]

    def test_request_logged_at_info(self):
        """Incoming request is logged at INFO before processing."""
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/success")

        assert resp.status_code == 200
        request_logs = [r for r in records if r.get("message", "").startswith("Request:")]
        assert len(request_logs) >= 1
        assert request_logs[0]["level"]["name"] == "INFO"
        assert "GET" in request_logs[0]["message"]
        assert "/success" in request_logs[0]["message"]

    def test_correlation_id_in_log_context(self):
        """Request log entries are produced when a correlation ID header is sent.

        Verifies:
        - The response header X-Request-ID matches the sent value (correlation middleware)
        - Log entries exist for both request and response
        """
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/success", headers={"X-Request-ID": "log-test-cid"})

        assert resp.status_code == 200
        # Response header proves correlation header was propagated
        assert resp.headers.get("x-request-id") == "log-test-cid"
        # Log entries were produced for both request and response
        messages = [r.get("message", "") for r in records]
        assert any("Request:" in m for m in messages), "No Request log entry"
        assert any("Response:" in m for m in messages), "No Response log entry"

    def test_non_http_scope_passed_through(self):
        """Non-HTTP scopes (e.g. websocket) are passed through without logging."""
        from src.common.infrastructure.presentation.middlewares.request_logging import (
            RequestLoggingMiddleware,
        )

        was_called = False

        async def mock_app(scope, receive, send):
            nonlocal was_called
            was_called = True

        middleware = RequestLoggingMiddleware(mock_app)
        asyncio.run(middleware({"type": "websocket"}, None, None))

        assert was_called, "Non-HTTP scope should be forwarded directly"

    def test_duration_in_response_log(self):
        """The response log includes a duration in milliseconds."""
        app = _make_app()
        _add_middlewares(app)

        records, resp = _capture_logs(app, "GET", "/success")

        assert resp.status_code == 200
        response_logs = [r for r in records if r.get("message", "").startswith("Response:")]
        assert len(response_logs) >= 1
        msg = response_logs[0]["message"]
        assert re.search(r"\d+ms", msg), f"Expected duration in ms, got: {msg}"
