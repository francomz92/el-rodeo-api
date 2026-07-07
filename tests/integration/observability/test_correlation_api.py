"""Integration tests for correlation ID propagation.

Verifies that X-Request-ID is echoed in responses, that UUIDs
are generated when no header is sent, and that the correlation_id
appears in log output.
"""

import re

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCorrelationIdIntegration:
    """Correlation ID behavior at the integration level."""

    async def test_custom_x_request_id_echoed(self, client: AsyncClient) -> None:
        """When X-Request-ID header is sent, the response echoes it."""
        resp = await client.get("/health", headers={"X-Request-ID": "abc-123"})
        assert resp.status_code in (200, 503)
        assert resp.headers.get("x-request-id") == "abc-123", f"Expected x-request-id: abc-123, got: {resp.headers.get('x-request-id')}"

    async def test_uuid_generated_when_no_header(self, client: AsyncClient) -> None:
        """When no X-Request-ID header, a 32-char UUID hex is generated."""
        resp = await client.get("/health")
        assert resp.status_code in (200, 503)
        cid = resp.headers.get("x-request-id", "")
        assert len(cid) == 32, f"Expected 32-char UUID, got '{cid}' (len={len(cid)})"
        assert re.fullmatch(r"[0-9a-f]{32}", cid), f"Expected hex string, got '{cid}'"

    async def test_correlation_id_in_log_output(self, client: AsyncClient) -> None:
        """The correlation ID appears in log entries.

        We capture Loguru output to verify the correlation_id is present.
        """
        import io

        from loguru import logger

        # Add a sink to capture log output
        sink = io.StringIO()
        handler_id = logger.add(sink, format="{extra[correlation_id]}", serialize=False)

        cid_value = "log-test-789"
        resp = await client.get("/health", headers={"X-Request-ID": cid_value})
        assert resp.status_code in (200, 503)

        # Remove the handler and check output
        logger.remove(handler_id)
        log_output = sink.getvalue()
        assert cid_value in log_output, f"Expected correlation_id '{cid_value}' in log output, got: {log_output[:500]}"
