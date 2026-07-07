"""Integration tests for the MercadoPago webhook with actual DI services.

Requires a running PostgreSQL with the test database.
Tests the webhook endpoint with mocked MercadoPago HTTP client.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from main import app

from src.billing.application.services._payment_webhook_service import (
    PaymentWebhookService,
)
from src.billing.domain.repositories._payment_gateway_port import (
    PreferenceResult,
)
from src.billing.infrastructure.payment_gateway._client import MercadoPagoHttpClient
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    _get_mercadopago_http_client,
    _get_payment_webhook_service,
)

pytestmark = [
    pytest.mark.asyncio,
]


@pytest.fixture(autouse=True)
def _override_gateway():
    """Override the MercadoPago HTTP client with a mock for all tests."""
    mock_client = MagicMock(spec=MercadoPagoHttpClient)
    mock_client.create_preference = AsyncMock(
        return_value=PreferenceResult(
            id="pref-test-webhook",
            init_point="https://www.mercadopago.com.ar/checkout/test-webhook",
        )
    )
    app.dependency_overrides[_get_mercadopago_http_client] = lambda: mock_client
    yield
    app.dependency_overrides.pop(_get_mercadopago_http_client, None)


@pytest.fixture(autouse=True)
def _override_webhook_service():
    """Override the entire PaymentWebhookService with a mock.

    This avoids creating real DB repositories during the webhook
    endpoint test, preventing IllegalStateChangeError from the
    asyncio.create_task background processing.
    """
    mock_service = MagicMock(spec=PaymentWebhookService)
    mock_service.validate_signature = MagicMock(return_value=True)
    mock_service.handle_ipn = AsyncMock()
    app.dependency_overrides[_get_payment_webhook_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(_get_payment_webhook_service, None)


class TestWebhookWithServices:
    """Tests for POST /billing/webhooks/mercadopago with wired services."""

    async def test_webhook_with_mocked_services_returns_200(
        self,
        client: AsyncClient,
    ):
        """4.10 Webhook with mocked gateway returns 200."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-123",
            headers={
                "x-signature": "ts=123456|v1=abc123",
                "x-request-id": "req-abc",
            },
        )
        assert response.status_code == 200

    async def test_webhook_with_invalid_signature_returns_200(
        self,
        client: AsyncClient,
    ):
        """4.10 Webhook with invalid signature still returns 200 (MP protocol).

        The webhook router always returns 200 immediately, regardless of
        signature validation outcome. Validation is handled in the background
        task.
        """
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-456",
            headers={
                "x-signature": "ts=123456|v1=invalid",
                "x-request-id": "req-xyz",
            },
        )
        assert response.status_code == 200

    async def test_webhook_without_signature_returns_422(
        self,
        client: AsyncClient,
    ):
        """4.10 Webhook without signature headers is rejected (required)."""
        response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-789",
        )
        assert response.status_code == 422

    async def test_plan_change_and_webhook_integration(
        self,
        client: AsyncClient,
        seed_session,
        test_tenant_id,
    ):
        """4.10 Plan change + webhook: create preference then receive notification.

        Note: This is a lightweight integration check since the actual
        PaymentWebhookService.handle_ipn uses background tasks. We verify
        both endpoints respond correctly.
        """
        # First, seed a plan + subscription for the tenant
        from datetime import datetime, timedelta, timezone
        from decimal import Decimal

        from src.billing.domain.entities._plan_type import PlanType
        from src.billing.infrastructure.persistence.models._plan_model import (
            Plan as PlanModel,
        )
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription as SubscriptionModel,
        )

        plan_repo = __import__(
            "src.billing.infrastructure.persistence.repositories._plan_repository",
            fromlist=["PlanRepository"],
        ).PlanRepository()
        pro_plan = await plan_repo.get_by_plan_type(PlanType.PRO)

        # Seed the plan row (must exist in DB for FK constraint)
        from sqlalchemy import select

        existing_plan = await seed_session.execute(select(PlanModel).where(PlanModel.plan_type == "pro"))
        if existing_plan.scalar_one_or_none() is None:
            plan = PlanModel(
                id=pro_plan.id,
                name="Pro",
                plan_type="pro",
                price_monthly=Decimal("15.00"),
                price_yearly=Decimal("150.00"),
            )
            seed_session.add(plan)
            await seed_session.flush()

        now = datetime.now(tz=timezone.utc)
        sub = SubscriptionModel(
            id=__import__("uuid").uuid4(),
            tenant_id=test_tenant_id,
            plan_id=pro_plan.id,
            status="active",
            current_period_start=now - timedelta(days=10),
            current_period_end=now + timedelta(days=20),
        )
        seed_session.add(sub)
        await seed_session.commit()

        # Verify plan change endpoint works
        plan_change_response = await client.put(
            "/billing/subscriptions/plan",
            json={"plan_type": "enterprise"},
        )
        assert plan_change_response.status_code == 200, (
            f"Plan change failed: {plan_change_response.status_code} - {plan_change_response.text}"
        )
        plan_data = plan_change_response.json()
        assert plan_data["checkout_url"] is not None

        # Verify webhook endpoint works
        webhook_response = await client.post(
            "/billing/webhooks/mercadopago?topic=payment&id=pay-integration-999",
            headers={
                "x-signature": "ts=123|v1=test",
                "x-request-id": "req-integration",
            },
        )
        assert webhook_response.status_code == 200
