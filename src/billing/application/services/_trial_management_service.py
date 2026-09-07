"""TrialManagementService — creates and manages trial subscriptions.

Provides methods to:
- start_trial: create a 14-day PRO trial for a new tenant
- cancel_subscription: cancel an active/trial subscription
- expire_trial: downgrade an expired trial to FREE plan
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.entities._subscription import Subscription
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.infrastructure.core._config import settings


class TrialManagementService:
    """Application service that manages trial subscription lifecycle."""

    async def start_trial(
        self,
        tenant_id: UUID,
        plan_repository: IPlanRepository,
        subscription_repository: ISubscriptionRepository,
        plan_type: PlanTypeEntity = PlanTypeEntity.PRO,
    ) -> Subscription:
        """Create a trial subscription for the given tenant.

        Fetches the plan by type, creates a TRIAL status subscription
        with trial_end = now + TRIAL_DAYS, and persists it.
        """
        plan = await plan_repository.get_by_plan_type(plan_type)
        if plan is None:
            raise ValueError(f"Plan not found: {plan_type.value}")
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

        return await subscription_repository.create(subscription)

    async def cancel_subscription(self, tenant_id: UUID, subscription_repository: ISubscriptionRepository) -> Subscription:
        """Cancel the current subscription for a tenant.

        Sets status to CANCELED and records the cancellation timestamp.
        Idempotent: if already canceled or expired, returns the subscription
        unchanged.
        """
        subscription = await subscription_repository.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        # Idempotent guard: skip if already canceled or expired
        if not subscription.can_cancel():
            return subscription

        updated = replace(
            subscription,
            status=SubscriptionStatus.CANCELED,
            canceled_at=datetime.now(timezone.utc),
        )
        return await subscription_repository.update(updated)

    async def expire_trial(
        self,
        tenant_id: UUID,
        subscription_repository: ISubscriptionRepository,
        plan_repository: IPlanRepository,
    ) -> Subscription:
        """Expire a trial subscription and downgrade to FREE plan.

        Sets status to EXPIRED and plan_id to the FREE plan.
        """
        subscription = await subscription_repository.get_by_tenant(tenant_id)
        if subscription is None:
            raise ValueError(f"No subscription found for tenant {tenant_id}")

        free_plan = await plan_repository.get_by_plan_type(PlanTypeEntity.FREE)
        if free_plan is None:
            raise ValueError("FREE plan not found")

        updated = replace(
            subscription,
            status=SubscriptionStatus.EXPIRED,
            plan_id=free_plan.id,
        )
        return await subscription_repository.update(updated)
