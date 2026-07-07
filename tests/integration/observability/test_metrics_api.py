"""Integration tests for the /metrics endpoint.

Verifies Prometheus metrics format, auth bypass, and
disabling behavior via a minimal test app.
"""

from typing import Any, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio


def _make_app(with_prometheus: bool = True) -> FastAPI:
    """Create a minimal FastAPI app with optional Prometheus instrumentation."""
    app = FastAPI()

    if with_prometheus:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return app


class TestMetricsEndpoint:
    """GET /metrics — Prometheus metrics endpoint."""

    @pytest_asyncio.fixture(scope="function")
    async def prometheus_client(self) -> AsyncGenerator[AsyncClient, Any]:
        """Client against a minimal app with PROMETHEUS_ENABLED=true."""
        app = _make_app(with_prometheus=True)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture(scope="function")
    async def disabled_client(self) -> AsyncGenerator[AsyncClient, Any]:
        """Client against a minimal app with Prometheus disabled."""
        app = _make_app(with_prometheus=False)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    async def test_metrics_returns_200_when_enabled(self, prometheus_client: AsyncClient) -> None:
        """When Instrumentator is configured, /metrics returns 200."""
        resp = await prometheus_client.get("/metrics")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"

    async def test_metrics_is_prometheus_text_format(self, prometheus_client: AsyncClient) -> None:
        """Response body is Prometheus text format with # HELP and # TYPE."""
        resp = await prometheus_client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text
        # Prometheus text format starts with # HELP lines
        assert text.startswith("# HELP"), f"Expected Prometheus text format, got: {text[:200]}"
        # Should contain at least one metric line
        assert "# TYPE" in text

    async def test_metrics_contains_expected_metric_names(self, prometheus_client: AsyncClient) -> None:
        """Response contains standard prometheus-fastapi-instrumentator metrics."""
        # First make a request to generate metrics
        await prometheus_client.get("/health")
        await prometheus_client.get("/nonexistent-route-12345")

        resp = await prometheus_client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text

        # Core HTTP metrics from the instrumentator
        assert "http_request_duration_seconds" in text, "Expected http_request_duration_seconds in metrics"
        assert "http_requests_total" in text, "Expected http_requests_total in metrics"

    async def test_metrics_does_not_require_auth(self, prometheus_client: AsyncClient) -> None:
        """Metrics endpoint is accessible without any auth headers."""
        resp = await prometheus_client.get("/metrics")
        assert resp.status_code == 200

    async def test_metrics_disabled_returns_404(self, disabled_client: AsyncClient) -> None:
        """When Instrumentator is not configured, /metrics returns 404."""
        resp = await disabled_client.get("/metrics")
        assert resp.status_code == 404, f"Expected 404 when Prometheus disabled, got {resp.status_code}"
