"""Tests for TrialManagementService.

Tests start_trial, cancel_subscription, and expire_trial methods.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus


class TestTrialManagementService:
    """TrialManagementService manages trial subscription lifecycle."""

    def setup_method(self) -> None:
        """Set up service with mocked repositories for each test."""
        self.plan_repo = MagicMock()
        self.subscription_repo = MagicMock()
        self.service = TrialManagementService(
            plan_repo=self.plan_repo,
            subscription_repo=self.subscription_repo,
        )
        self.pro_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.PRO,
            name="Pro",
            description="Plan profesional",
            features=[Feature(name="api_access")],
            quotas=[Quota(name="animals", limit=500)],
        )
        self.free_plan = Plan(
            id=uuid4(),
            plan_type=PlanType.FREE,
            name="Free",
            description="Plan gratuito",
            features=[],
            quotas=[Quota(name="animals", limit=50)],
        )

    @pytest.mark.asyncio
    async def test_start_trial_creates_subscription_with_trial_status_and_pro_plan(
        self,
    ) -> None:
        """3.1 start_trial creates TRIAL subscription linked to PRO plan and tenant."""
        tenant_id = uuid4()
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=self.pro_plan)
        self.subscription_repo.create = AsyncMock(side_effect=lambda sub: sub)

        result = await self.service.start_trial(tenant_id)

        assert result.status == SubscriptionStatus.TRIAL
        assert result.plan_id == self.pro_plan.id
        assert result.tenant_id == tenant_id
        assert result.trial_end is not None
        self.plan_repo.get_by_plan_type.assert_awaited_once_with(PlanType.PRO)
        self.subscription_repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_trial_uses_correct_trial_duration(self) -> None:
        """3.1 Trial duration should match settings.TRIAL_DAYS (default 14)."""
        from src.common.infrastructure.core._config import settings

        tenant_id = uuid4()
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=self.pro_plan)
        self.subscription_repo.create = AsyncMock(side_effect=lambda sub: sub)

        result = await self.service.start_trial(tenant_id)

        assert result.trial_end is not None
        expected_duration = timedelta(days=settings.TRIAL_DAYS)
        actual_duration = result.trial_end - result.current_period_start
        # Allow slight time diff due to execution time (< 2 seconds)
        assert abs((actual_duration - expected_duration).total_seconds()) < 2

    @pytest.mark.asyncio
    async def test_cancel_subscription_sets_canceled_status(self) -> None:
        """3.1 cancel_subscription sets status=CANCELED and records canceled_at."""
        tenant_id = uuid4()
        existing_sub = Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=datetime.now(timezone.utc),
        )
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=existing_sub)
        self.subscription_repo.update = AsyncMock(side_effect=lambda sub: sub)

        result = await self.service.cancel_subscription(tenant_id)

        assert result.status == SubscriptionStatus.CANCELED
        assert result.canceled_at is not None
        self.subscription_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_expire_trial_changes_to_free_plan(self) -> None:
        """3.1 expire_trial sets status=EXPIRED and plan_id to FREE plan."""
        tenant_id = uuid4()
        existing_sub = Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=self.pro_plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=datetime.now(timezone.utc),
        )
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=existing_sub)
        self.plan_repo.get_by_plan_type = AsyncMock(return_value=self.free_plan)
        self.subscription_repo.update = AsyncMock(side_effect=lambda sub: sub)

        result = await self.service.expire_trial(tenant_id)

        assert result.status == SubscriptionStatus.EXPIRED
        assert result.plan_id == self.free_plan.id
        self.plan_repo.get_by_plan_type.assert_awaited_once_with(PlanType.FREE)
        self.subscription_repo.update.assert_awaited_once()
