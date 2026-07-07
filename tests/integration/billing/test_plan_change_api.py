"""Integration tests for PUT /billing/subscriptions/plan.

Requires a running PostgreSQL with the test database.
The client fixture from tests/integration/conftest.py bypasses auth
and provides a tenant, user, and DB connection.

Env: MP_ACCESS_TOKEN must be configured (or gateway must be overridden).
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from main import app

from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories._payment_gateway_port import (
    PreferenceResult,
)
from src.billing.infrastructure.payment_gateway._client import MercadoPagoHttpClient
from src.billing.infrastructure.persistence.models._subscription_model import (
    Subscription as SubscriptionModel,
)
from src.billing.infrastructure.persistence.repositories._plan_repository import (
    PlanRepository,
)
from src.billing.infrastructure.presentation.dependencies._billing_dependencies import (
    _get_mercadopago_http_client,
    _get_plan_repository,
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
            id="pref-test-123",
            init_point="https://www.mercadopago.com.ar/checkout/test",
        )
    )
    app.dependency_overrides[_get_mercadopago_http_client] = lambda: mock_client
    yield
    app.dependency_overrides.pop(_get_mercadopago_http_client, None)


@pytest.fixture(autouse=True)
def _override_plan_repo():
    """Use a shared PlanRepository so we know the plan IDs for seeding."""
    plan_repo = PlanRepository()
    app.dependency_overrides[_get_plan_repository] = lambda: plan_repo
    yield plan_repo
    app.dependency_overrides.pop(_get_plan_repository, None)


async def _seed_plan(
    seed_session,
    plan_repo: PlanRepository,
    plan_type: PlanType = PlanType.PRO,
) -> UUID:
    """Seed a plan row in the DB if it doesn't already exist.

    Returns the plan's DB id (inserted or from the in-memory repo).
    """
    from sqlalchemy import select

    from src.billing.infrastructure.persistence.models._plan_model import (
        Plan as PlanModel,
    )

    existing = await seed_session.execute(select(PlanModel).where(PlanModel.plan_type == plan_type.value))
    existing_plan = existing.scalar_one_or_none()
    if existing_plan is not None:
        return existing_plan.id

    plan_entity = await plan_repo.get_by_plan_type(plan_type)
    plan = PlanModel(
        id=plan_entity.id,
        name=plan_entity.name,
        plan_type=plan_entity.plan_type.value,
        price_monthly=plan_entity.price_monthly.amount,
        price_yearly=(plan_entity.price_yearly.amount if plan_entity.price_yearly else None),
    )
    seed_session.add(plan)
    await seed_session.commit()
    return plan_entity.id


async def _seed_subscription(
    seed_session,
    tenant_id,
    plan_repo: PlanRepository,
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
):
    """Insert a subscription row for integration tests."""
    plan_id = await _seed_plan(seed_session, plan_repo)
    pro_plan = await plan_repo.get_by_plan_type(PlanType.PRO)
    now = datetime.now(tz=timezone.utc)
    sub = SubscriptionModel(
        id=uuid4(),
        tenant_id=tenant_id,
        plan_id=plan_id,
        status=status.value,
        current_period_start=now - timedelta(days=10),
        current_period_end=now + timedelta(days=20),
    )
    seed_session.add(sub)
    await seed_session.commit()
    return sub, pro_plan


class TestPlanChangeApi:
    """Tests for PUT /billing/subscriptions/plan."""

    async def test_upgrade_returns_checkout_url(
        self,
        client: AsyncClient,
        seed_session,
        test_tenant_id,
        _override_plan_repo: PlanRepository,
    ):
        """4.8 Upgrade to a paid plan returns a MercadoPago checkout URL."""
        await _seed_subscription(seed_session, test_tenant_id, _override_plan_repo)

        response = await client.put(
            "/billing/subscriptions/plan",
            json={"plan_type": "enterprise"},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "checkout_url" in data
        assert data["checkout_url"] is not None
        assert "subscription" in data
        assert data["subscription"]["status"] == "active"

    async def test_reject_free_plan(
        self,
        client: AsyncClient,
        seed_session,
        test_tenant_id,
        _override_plan_repo: PlanRepository,
    ):
        """4.8 Selecting FREE plan is rejected (422)."""
        await _seed_subscription(seed_session, test_tenant_id, _override_plan_repo)

        response = await client.put(
            "/billing/subscriptions/plan",
            json={"plan_type": "free"},
        )

        assert response.status_code == 422, response.text
        data = response.json()
        assert "FREE plan cannot be selected" in data.get("detail", "")

    async def test_reject_unauthenticated(
        self,
        seed_session,
        test_tenant_id,
        _override_plan_repo: PlanRepository,
    ):
        """4.8 Request without valid auth returns 401/403."""
        from tests.integration.conftest import app as _test_app

        transport = __import__("httpx").ASGITransport(app=_test_app)
        async with __import__("httpx").AsyncClient(transport=transport, base_url="http://test") as anon_client:
            await _seed_subscription(seed_session, test_tenant_id, _override_plan_repo)
            response = await anon_client.put(
                "/billing/subscriptions/plan",
                json={"plan_type": "pro"},
            )

            assert response.status_code in (401, 403)

    async def test_reject_same_plan(
        self,
        client: AsyncClient,
        seed_session,
        test_tenant_id,
        _override_plan_repo: PlanRepository,
    ):
        """4.8 Changing to the same plan is a no-op (returns current sub, no url)."""
        sub, pro_plan = await _seed_subscription(seed_session, test_tenant_id, _override_plan_repo)

        response = await client.put(
            "/billing/subscriptions/plan",
            json={"plan_type": "pro"},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["checkout_url"] is None
        assert data["subscription"]["plan_id"] == str(pro_plan.id)
