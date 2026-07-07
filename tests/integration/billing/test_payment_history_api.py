"""Integration tests for GET /billing/payments.

Requires a running PostgreSQL with the test database.
The client fixture from tests/integration/conftest.py bypasses auth
and provides a tenant, user, and DB connection.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.infrastructure.persistence.models._payment_model import (
    Payment as PaymentModel,
)
from src.billing.infrastructure.persistence.models._subscription_model import (
    Subscription as SubscriptionModel,
)
from src.billing.infrastructure.persistence.repositories._plan_repository import (
    PlanRepository,
)

pytestmark = [
    pytest.mark.asyncio,
]


async def _seed_plan_and_subscription(
    seed_session,
    tenant_id,
) -> UUID:
    """Create a plan + subscription row and return the subscription ID.

    Uses PlanRepository's deterministic plan IDs so cross-test lookups work.
    """
    from sqlalchemy import select

    from src.billing.domain.entities._plan_type import PlanType
    from src.billing.infrastructure.persistence.models._plan_model import (
        Plan as PlanModel,
    )

    sub_id = uuid4()
    now = datetime.now(tz=timezone.utc)

    # Use stable plan ID from the PlanRepository seed data
    plan_repo = PlanRepository()
    pro_plan = await plan_repo.get_by_plan_type(PlanType.PRO)
    plan_id = pro_plan.id

    # Check if a plan already exists (shared DB across tests in a session)
    existing = await seed_session.execute(select(PlanModel).where(PlanModel.plan_type == "pro"))
    if existing.scalar_one_or_none() is None:
        plan = PlanModel(
            id=plan_id,
            name="Test Plan",
            plan_type="pro",
            price_monthly=Decimal("15.00"),
            price_yearly=Decimal("150.00"),
        )
        seed_session.add(plan)
        await seed_session.flush()

    sub = SubscriptionModel(
        id=sub_id,
        tenant_id=tenant_id,
        plan_id=plan_id,
        status="active",
        current_period_start=now - timedelta(days=10),
        current_period_end=now + timedelta(days=20),
    )
    seed_session.add(sub)
    await seed_session.commit()
    return sub_id


async def _seed_payments(
    seed_session,
    tenant_id,
    count: int = 3,
    sub_id=None,
) -> list:
    """Insert payment rows for a tenant and return their models."""
    if sub_id is None:
        sub_id = uuid4()
    now = datetime.now(tz=timezone.utc)
    payments = []
    for i in range(count):
        pm = PaymentModel(
            id=uuid4(),
            tenant_id=tenant_id,
            subscription_id=sub_id,
            status=PaymentStatus.APPROVED.value,
            amount=Decimal(f"{15 + i}.00"),
            currency="ARS",
            description=f"Plan Pro payment {i + 1}",
        )
        seed_session.add(pm)
        payments.append(pm)
    await seed_session.commit()
    return payments


class TestPaymentHistoryApi:
    """Tests for GET /billing/payments."""

    async def test_returns_paginated_payments(
        self,
        client: AsyncClient,
        seed_session,
        test_tenant_id,
    ):
        """4.9 Paginated payments are returned correctly."""
        sub_id = await _seed_plan_and_subscription(seed_session, test_tenant_id)
        await _seed_payments(seed_session, test_tenant_id, count=3, sub_id=sub_id)

        response = await client.get("/billing/payments?page=1&per_page=2")

        assert response.status_code == 200, response.text
        data = response.json()
        assert "payments" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["payments"]) == 2
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["per_page"] == 2

    async def test_returns_empty_list_for_new_tenant(
        self,
        client: AsyncClient,
    ):
        """4.9 A tenant with no payments gets an empty list."""
        response = await client.get("/billing/payments")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["payments"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20

    async def test_reject_unauthenticated(
        self,
    ):
        """4.9 Request without valid auth returns 401/403."""
        from tests.integration.conftest import app as _test_app

        transport = __import__("httpx").ASGITransport(app=_test_app)
        async with __import__("httpx").AsyncClient(transport=transport, base_url="http://test") as anon_client:
            response = await anon_client.get("/billing/payments")
            assert response.status_code in (401, 403)

    async def test_pagination_defaults(
        self,
        client: AsyncClient,
    ):
        """4.9 Default page/per_page values are applied."""
        response = await client.get("/billing/payments")

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 20
