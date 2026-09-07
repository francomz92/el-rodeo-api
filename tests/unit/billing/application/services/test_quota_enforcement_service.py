"""Tests for QuotaEnforcementService.

Tests check_quota behavior with different quota conditions:
- Under limit passes
- Over limit raises QuotaExceededException
- skip_check bypasses enforcement
- Unlimited quota (-1) never raises
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.billing.application.services._quota_enforcement_service import (
    QuotaEnforcementService,
)
from src.billing.domain.entities._feature import Feature
from src.billing.domain.entities._plan import Plan
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._quota import Quota
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import QuotaExceededException


class TestQuotaEnforcementService:
    """QuotaEnforcementService checks resource quotas against plan limits."""

    def setup_method(self) -> None:
        """Set up service with mocked repositories for each test."""
        self.plan_repo = MagicMock()
        self.subscription_repo = MagicMock()
        self.service = QuotaEnforcementService(
            plan_repo=self.plan_repo,
            subscription_repo=self.subscription_repo,
        )
        self.tenant_id = uuid4()
        self.plan_with_quotas = Plan(
            id=uuid4(),
            plan_type=PlanType.PRO,
            name="Pro",
            description="Pro plan with quotas",
            features=[Feature(name="api_access")],
            quotas=[
                Quota(name="animals", limit=500, description="Max animals"),
                Quota(name="users", limit=25, description="Max users"),
                Quota(name="storage", limit=-1, description="Unlimited storage"),
            ],
        )
        self.active_subscription = Subscription(
            id=uuid4(),
            tenant_id=self.tenant_id,
            plan_id=self.plan_with_quotas.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
            metadata={"animals": 10, "users": 3, "storage": 100},
        )

    @pytest.mark.asyncio
    async def test_check_quota_passes_when_under_limit(self) -> None:
        """Should return None when current usage + delta is within limit."""
        self.subscription_repo.get_by_tenant = AsyncMock(
            return_value=self.active_subscription,
        )
        self.plan_repo.get_by_id = AsyncMock(return_value=self.plan_with_quotas)

        result = await self.service.check_quota(
            tenant_id=self.tenant_id,
            resource="animals",
            delta=1,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_check_quota_raises_when_over_limit(self) -> None:
        """Should raise QuotaExceededException when delta exceeds limit."""
        sub_at_limit = Subscription(
            id=self.active_subscription.id,
            tenant_id=self.tenant_id,
            plan_id=self.plan_with_quotas.id,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=self.active_subscription.current_period_start,
            current_period_end=self.active_subscription.current_period_end,
            metadata={"animals": 500, "users": 3},  # animals already at limit
        )
        self.subscription_repo.get_by_tenant = AsyncMock(return_value=sub_at_limit)
        self.plan_repo.get_by_id = AsyncMock(return_value=self.plan_with_quotas)

        with pytest.raises(QuotaExceededException) as exc_info:
            await self.service.check_quota(
                tenant_id=self.tenant_id,
                resource="animals",
                delta=1,
            )

        assert exc_info.value.resource_name == "animals"
        assert exc_info.value.limit == 500
        assert exc_info.value.current_usage == 500

    @pytest.mark.asyncio
    async def test_skip_check_bypasses_enforcement(self) -> None:
        """Should return None immediately when skip_check=True, no repos called."""
        # get_by_tenant should NOT be called when skip_check is True
        self.subscription_repo.get_by_tenant = AsyncMock()

        result = await self.service.check_quota(
            tenant_id=self.tenant_id,
            resource="animals",
            delta=999999,
            skip_check=True,
        )

        assert result is None
        self.subscription_repo.get_by_tenant.assert_not_called()

    @pytest.mark.asyncio
    async def test_unlimited_quota_never_raises(self) -> None:
        """Should pass when quota limit is -1 (unlimited) regardless of usage."""
        self.subscription_repo.get_by_tenant = AsyncMock(
            return_value=self.active_subscription,
        )
        self.plan_repo.get_by_id = AsyncMock(return_value=self.plan_with_quotas)

        result = await self.service.check_quota(
            tenant_id=self.tenant_id,
            resource="storage",
            delta=999999,
        )

        assert result is None
