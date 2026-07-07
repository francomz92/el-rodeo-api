"""Tests for ChangePlanService.

Tests plan change rules:
- FREE plan selection is rejected
- TRIAL subscription cannot change plan
- Same plan is a no-op
- Upgrade (PRO → ENTERPRISE) creates checkout preference
- Downgrade from paid plan to free-like applies immediately
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._change_plan_service import (
    ChangePlanService,
)
from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.value_objects._money import Money


class TestChangePlanService:
    """ChangePlanService enforces plan change business rules."""

    def setup_method(self) -> None:
        """Set up service with mocked repositories for each test."""
        self.plan_repo = MagicMock()
        self.sub_repo = MagicMock()
        self.mp_service = MagicMock()
        self.uow = MagicMock()

        self.service = ChangePlanService(
            plan_repo=self.plan_repo,
            sub_repo=self.sub_repo,
            mercado_pago_service=self.mp_service,
            uow_factory=self.uow,
        )

        self.tenant_id = uuid4()
        now = datetime.now(timezone.utc)

        self.pro_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.PRO,
            name="Pro",
            description="Plan profesional",
            features=[Feature(name="api_access")],
            quotas=[Quota(name="animals", limit=500)],
            price_monthly=Money(amount=Decimal("15.00")),
        )
        self.enterprise_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.ENTERPRISE,
            name="Enterprise",
            description="Plan empresarial",
            features=[Feature(name="api_access")],
            quotas=[Quota(name="animals", limit=999999)],
            price_monthly=Money(amount=Decimal("50.00")),
        )

        self.active_subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now - timedelta(days=10),
            current_period_end=now + timedelta(days=20),
        )

        self.trial_subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=now - timedelta(days=5),
            current_period_end=now + timedelta(days=9),
            trial_end=now + timedelta(days=9),
        )

    # ---- GUARD: FREE selection -------------------------------------------------

    @pytest.mark.asyncio
    async def test_rejects_free_plan_selection(self) -> None:
        """3.6 FREE plan is not selectable as a target."""
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.pro_plan)

        with pytest.raises(PlanNotChangeableError, match="FREE plan cannot be selected"):
            await self.service.change_plan(self.tenant_id, PlanType.FREE)

        self.sub_repo.update.assert_not_called()
        self.mp_service.create_checkout_preference.assert_not_called()

    # ---- GUARD: TRIAL rejection -------------------------------------------------

    @pytest.mark.asyncio
    async def test_rejects_trial_subscription_plan_change(self) -> None:
        """3.6 TRIAL subscriptions cannot change plan."""
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.trial_subscription)

        with pytest.raises(
            PlanNotChangeableError,
            match="Trial subscriptions cannot change plan",
        ):
            await self.service.change_plan(self.tenant_id, PlanType.ENTERPRISE)

        self.sub_repo.update.assert_not_called()
        self.mp_service.create_checkout_preference.assert_not_called()

    # ---- Same plan → no-op ------------------------------------------------------

    @pytest.mark.asyncio
    async def test_same_plan_is_no_op(self) -> None:
        """3.6 Changing to the same plan returns current sub with no preference."""
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.pro_plan)

        sub, init_point = await self.service.change_plan(self.tenant_id, PlanType.PRO)

        assert sub == self.active_subscription
        assert init_point is None
        self.sub_repo.update.assert_not_called()
        self.mp_service.create_checkout_preference.assert_not_called()

    # ---- Upgrade: PRO → ENTERPRISE (paid → higher-paid) ------------------------

    @pytest.mark.asyncio
    async def test_upgrade_to_enterprise_creates_checkout_preference(self) -> None:
        """3.6 Upgrade to ENTERPRISE creates MP preference and returns init_point."""
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.pro_plan)
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=self.enterprise_plan)
        self.mp_service.create_checkout_preference = AsyncMock(return_value="https://mp.com/checkout/pref-123")

        sub, init_point = await self.service.change_plan(self.tenant_id, PlanType.ENTERPRISE)

        # Subscription is NOT updated yet — wait for payment approval
        assert sub == self.active_subscription
        assert init_point == "https://mp.com/checkout/pref-123"
        self.mp_service.create_checkout_preference.assert_awaited_once_with(self.tenant_id, PlanType.ENTERPRISE)
        self.sub_repo.update.assert_not_called()

    # ---- Downgrade: paid plan → free-like (price = 0) ---------------------------

    @pytest.mark.asyncio
    async def test_downgrade_to_free_like_applies_immediately(self) -> None:
        """3.6 Downgrade to a plan with zero/no price applies immediately."""
        no_price_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.ENTERPRISE,
            name="Enterprise-Free",
            description="Enterprise without price (hypothetical)",
            features=[],
            quotas=[Quota(name="animals", limit=10)],
            price_monthly=None,
        )
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.pro_plan)
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=no_price_plan)
        self.sub_repo.update = AsyncMock(side_effect=lambda sub: sub)

        sub, init_point = await self.service.change_plan(self.tenant_id, PlanType.ENTERPRISE)

        assert init_point is None
        assert sub.plan_id == no_price_plan.id
        self.sub_repo.update.assert_awaited_once()
        self.mp_service.create_checkout_preference.assert_not_called()

    # ---- Non-ACTIVE status rejection -------------------------------------------

    @pytest.mark.asyncio
    async def test_non_active_subscription_cannot_change_plan(self) -> None:
        """3.6 Subscriptions with non-ACTIVE status (other than TRIAL) rejected."""
        canceled_sub = replace(
            self.active_subscription,
            status=SubscriptionStatus.CANCELED,
        )
        self.sub_repo.get_by_tenant = AsyncMock(return_value=canceled_sub)

        with pytest.raises(PlanNotChangeableError, match="cannot change plan"):
            await self.service.change_plan(self.tenant_id, PlanType.ENTERPRISE)

        self.sub_repo.update.assert_not_called()

    # ---- No subscription found -------------------------------------------------

    @pytest.mark.asyncio
    async def test_no_subscription_raises_value_error(self) -> None:
        """3.6 Missing subscription raises ValueError."""
        self.sub_repo.get_by_tenant = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="No subscription found"):
            await self.service.change_plan(self.tenant_id, PlanType.PRO)

    # ---- MP service unavailable for upgrade ------------------------------------

    @pytest.mark.asyncio
    async def test_upgrade_without_mp_service_raises_error(self) -> None:
        """3.6 Upgrade when MercadoPagoService is None raises error."""
        service_no_mp = ChangePlanService(
            plan_repo=self.plan_repo,
            sub_repo=self.sub_repo,
            mercado_pago_service=None,
            uow_factory=self.uow,
        )
        self.sub_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.pro_plan)
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=self.enterprise_plan)

        with pytest.raises(
            PlanNotChangeableError,
            match="Payment gateway is not configured",
        ):
            await service_no_mp.change_plan(self.tenant_id, PlanType.ENTERPRISE)
