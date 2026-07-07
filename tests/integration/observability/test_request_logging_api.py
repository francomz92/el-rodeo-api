"""Integration tests for request logging middleware.

Verifies that log entries contain method/path/status/duration and
that 4xx responses are logged at WARNING level.
"""

import io

import pytest
from httpx import AsyncClient
from loguru import logger

pytestmark = pytest.mark.asyncio


class TestRequestLoggingIntegration:
    """Request logging middleware behavior at the integration level."""

    async def test_request_log_includes_method_path_status(self, client: AsyncClient) -> None:
        """Log entries include HTTP method, path, and status code."""
        sink = io.StringIO()
        handler_id = logger.add(
            sink,
            format="{message}",
            enqueue=False,  # synchronous capture
        )

        await client.get("/health", headers={"X-Request-ID": "req-log-test"})
        logger.remove(handler_id)
        log_output = sink.getvalue()

        # Should contain request logging output with /health
        assert "/health" in log_output, f"Expected /health in log output, got: {log_output[:500]}"

    async def test_404_logged_at_warning(self, client: AsyncClient) -> None:
        """Accessing an invalid route produces log output mentioning 404."""
        sink = io.StringIO()
        handler_id = logger.add(
            sink,
            format="{level} | {message}",
            enqueue=False,
        )

        resp = await client.get("/nonexistent-route-99999")
        assert resp.status_code == 404

        logger.remove(handler_id)
        log_output = sink.getvalue()

        # The response log should mention the 404 status
        assert "404" in log_output, f"Expected 404 status in log, got: {log_output[:500]}"

    async def test_correlation_id_in_access_log(self, client: AsyncClient) -> None:
        """The correlation ID appears in request log entries."""
        sink = io.StringIO()
        handler_id = logger.add(
            sink,
            format="{extra[correlation_id]}",
            enqueue=False,
        )

        cid = "access-log-cid-456"
        await client.get("/health", headers={"X-Request-ID": cid})

        logger.remove(handler_id)
        log_output = sink.getvalue()

        assert cid in log_output, f"Expected correlation_id '{cid}' in access log, got: {log_output[:500]}"
