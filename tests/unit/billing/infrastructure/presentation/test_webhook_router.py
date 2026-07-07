"""Tests for the MercadoPago webhook router."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.billing.application.services._payment_webhook_service import (
    PaymentWebhookService,
)
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    _get_payment_webhook_service,
)
from src.billing.infrastructure.presentation.routers._webhook_router import (
    webhook_router,
)


@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI app with just the webhook router."""
    application = FastAPI()
    application.include_router(webhook_router)

    # Override the PaymentWebhookService dependency with a mock
    mock_webhook_service = MagicMock(spec=PaymentWebhookService)
    mock_webhook_service.handle_ipn = AsyncMock()
    application.dependency_overrides[_get_payment_webhook_service] = lambda: mock_webhook_service

    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestWebhookRouter:
    """Tests for POST /billing/webhooks/mercadopago."""

    @pytest.mark.asyncio
    async def test_webhook_returns_200(self, client: AsyncClient) -> None:
        """A valid webhook request returns 200 OK."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-123",
            headers={
                "x-signature": "ts=123456|v1=abc123",
                "x-request-id": "req-abc",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_without_signature_returns_422(self, client: AsyncClient) -> None:
        """Webhook without signature headers is rejected (required)."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-123",
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_with_invalid_topic_returns_200(self, client: AsyncClient) -> None:
        """Even an unsupported topic returns 200 (MP expects this)."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=unknown&id=123",
            headers={
                "x-signature": "ts=123|v1=valid",
                "x-request-id": "req-abc",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_with_merchant_order_returns_200(self, client: AsyncClient) -> None:
        """Merchant order topic also returns 200 (handled in future)."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=merchant_order&id=123",
            headers={
                "x-signature": "ts=123|v1=valid",
                "x-request-id": "req-abc",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_without_topic_returns_422(self, client: AsyncClient) -> None:
        """Missing required 'topic' query param returns 422."""
        response = await client.post(
            "/billing/webhooks/mercadopago?id=pay-123",
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_without_id_returns_422(self, client: AsyncClient) -> None:
        """Missing required 'id' query param returns 422."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment",
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_allows_only_post(self, client: AsyncClient) -> None:
        """GET on the webhook endpoint returns 405 (method not allowed)."""
        response = await client.get(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-123",
        )
        assert response.status_code == 405
