"""TrialManagementService — creates and manages trial subscriptions.

Provides methods to:
- start_trial: create a 14-day PRO trial for a new tenant
- cancel_subscription: cancel an active/trial subscription
- expire_trial: downgrade an expired trial to FREE plan
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.billing.domain.entities._plan_type import PlanType
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.infrastructure.core._config import settings


class TrialManagementService:
    """Application service that manages trial subscription lifecycle."""

    def __init__(
        self,
        plan_repo: IPlanRepository,
        subscription_repo: ISubscriptionRepository,
        tenant_repo: ITenantRepository,
    ) -> None:
        self._plan_repo = plan_repo
        self._subscription_repo = subscription_repo
        self._tenant_repo = tenant_repo

    async def start_trial(
        self,
        tenant_id: UUID,
        plan_type: PlanType = PlanType.PRO,
    ) -> Subscription:
        """Create a trial subscription for the given tenant.

        Fetches the plan by type, creates a TRIAL status subscription
        with trial_end = now + TRIAL_DAYS, persists it, and updates
        the tenant's plan_id.
        """
        plan = await self._plan_repo.get_by_plan_type(plan_type)
        now = datetime.now(timezone.utc)
        trial_end = now + timedelta(days=settings.TRIAL_DAYS)

        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            current_period_start=now,
            current_period_end=trial_end,
            trial_end=trial_end,
        )

        created = await self._subscription_repo.create(subscription)
        await self._tenant_repo.update(tenant_id, plan_id=plan.id)
        return created

    async def cancel_subscription(self, tenant_id: UUID) -> Subscription:
        """Cancel the current subscription for a tenant.

        Sets status to CANCELED and records the cancellation timestamp.
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        updated = replace(
            subscription,
            status=SubscriptionStatus.CANCELED,
            canceled_at=datetime.now(timezone.utc),
        )
        return await self._subscription_repo.update(updated)

    async def expire_trial(self, tenant_id: UUID) -> Subscription:
        """Expire a trial subscription and downgrade to FREE plan.

        Sets status to EXPIRED, plan_id to the FREE plan, and updates
        the tenant's plan_id accordingly.
        """
        subscription = await self._subscription_repo.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        free_plan = await self._plan_repo.get_by_plan_type(PlanType.FREE)

        updated = replace(
            subscription,
            status=SubscriptionStatus.EXPIRED,
            plan_id=free_plan.id,
        )
        result = await self._subscription_repo.update(updated)
        await self._tenant_repo.update(tenant_id, plan_id=free_plan.id)
        return result
