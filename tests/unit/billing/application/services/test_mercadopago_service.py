"""Tests for MercadoPagoService.create_checkout_preference.

Tests:
- Successful preference creation returns init_point
- Rejection of plan with zero/no price
- Payment record saved with PENDING status
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._mercadopago_service import (
    MercadoPagoService,
)
from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PlanNotChangeableError
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    ISubscriptionRepository,
    PreferenceResult,
)
from src.billing.domain.value_objects._money import Money
from src.billing.infrastructure.persistence.repositories import PlanRepository
from src.common.application.ports.uow import IUoW


class TestMercadoPagoServiceCreatePreference:
    """MercadoPagoService.create_checkout_preference orchestrates MP flow."""

    def setup_method(self) -> None:
        """Set up service with mocked gateway, repos, and UoW."""
        self.gateway = MagicMock(spec=IPaymentGateway)
        self.payment_repo = MagicMock(spec=IPaymentRepository)
        self.subscription_repo = MagicMock(spec=ISubscriptionRepository)
        self.plan_repo = PlanRepository()
        self.uow = MagicMock(spec=IUoW)

        self.service = MercadoPagoService(
            gateway=self.gateway,
            payment_repo=self.payment_repo,
            subscription_repo=self.subscription_repo,
            plan_repo=self.plan_repo,
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

        self.active_subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now - timedelta(days=10),
            current_period_end=now + timedelta(days=20),
        )

        self.preference_result = PreferenceResult(
            id="pref-123",
            init_point="https://www.mercadopago.com.ar/checkout/pref-123",
        )

    def _setup_plan_repo(self, plan: Plan) -> None:
        """Configure the plan repo mock to return ``plan`` for any plan_type."""
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=plan)  # type: ignore[assignment]

    # ---- Successful preference creation ----------------------------------------

    @pytest.mark.asyncio
    async def test_creates_preference_through_gateway_and_returns_init_point(
        self,
    ) -> None:
        """3.7 create_checkout_preference returns init_point from gateway."""
        self._setup_plan_repo(self.pro_plan)
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=self.active_subscription)
        self.gateway.create_preference = AsyncMock(return_value=self.preference_result)
        self.payment_repo.create = AsyncMock(side_effect=lambda p: p)

        init_point = await self.service.create_checkout_preference(self.tenant_id, PlanType.PRO)

        assert init_point == self.preference_result.init_point

        # Verify gateway call
        self.gateway.create_preference.assert_awaited_once()
        call_args = self.gateway.create_preference.await_args
        assert call_args is not None
        kwargs = call_args.kwargs
        assert len(kwargs["items"]) == 1
        assert kwargs["items"][0].unit_price == Decimal("15.00")
        assert kwargs["items"][0].title == "Plan Pro - El Rodeo"
        assert kwargs["external_reference"] == f"{self.tenant_id}:{PlanType.PRO.value}"

        # Verify payment record saved
        self.payment_repo.create.assert_awaited_once()
        payment = self.payment_repo.create.await_args.args[0]
        assert payment.status == PaymentStatus.PENDING
        assert payment.tenant_id == self.tenant_id
        assert payment.subscription_id == self.active_subscription.id
        assert payment.amount == Decimal("15.00")
        assert payment.mp_preference_id == "pref-123"

    # ---- Rejection of zero/no price plan ---------------------------------------

    @pytest.mark.asyncio
    async def test_rejects_plan_with_zero_price(self) -> None:
        """3.7 Plan with price <= 0 raises PlanNotChangeableError."""
        no_price_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.FREE,
            name="Free",
            description="Gratuito",
            features=[],
            quotas=[Quota(name="animals", limit=50)],
            price_monthly=None,
        )
        self._setup_plan_repo(no_price_plan)

        with pytest.raises(PlanNotChangeableError, match="FREE plan cannot be purchased"):
            await self.service.create_checkout_preference(self.tenant_id, PlanType.FREE)

        self.gateway.create_preference.assert_not_called()
        self.payment_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_rejects_plan_with_zero_amount(self) -> None:
        """3.7 Plan with price_monthly=0 raises PlanNotChangeableError."""
        zero_price_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.FREE,
            name="Free",
            description="Gratuito",
            features=[],
            quotas=[Quota(name="animals", limit=50)],
            price_monthly=Money(amount=Decimal("0.00")),
        )
        self._setup_plan_repo(zero_price_plan)

        with pytest.raises(PlanNotChangeableError, match="FREE plan cannot be purchased"):
            await self.service.create_checkout_preference(self.tenant_id, PlanType.FREE)

        self.gateway.create_preference.assert_not_called()
        self.payment_repo.create.assert_not_called()

    # ---- No subscription raises ValueError -------------------------------------

    @pytest.mark.asyncio
    async def test_no_subscription_raises_value_error(self) -> None:
        """3.7 Missing subscription raises ValueError."""
        self._setup_plan_repo(self.pro_plan)
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="No subscription found"):
            await self.service.create_checkout_preference(self.tenant_id, PlanType.PRO)
