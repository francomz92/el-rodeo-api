"""CheckQuotaCase — checks resource quotas against plan limits.

Provides execute to enforce plan-level limits on resource usage.
Raises QuotaExceededException when a tenant exceeds their plan quota.
Supports skip_check flag for admin/internal bypass and -1 (unlimited)
quota values.
"""

from uuid import UUID

from src.billing.domain.exceptions import QuotaExceededException
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.application.ports.uow import IUoW


class CheckQuotaCase:
    """Use case that enforces resource quotas per plan."""

    def __init__(
        self,
        uow: IUoW,
    ) -> None:
        self.uow = uow

    async def execute(
        self,
        tenant_id: UUID,
        resource: str,
        delta: int = 1,
        skip_check: bool = False,
    ) -> None:
        """Check if a tenant has quota available for the given resource.

        Args:
            tenant_id: The tenant to check quota for.
            resource: The resource name to check (e.g. "animals", "users").
            delta: The amount of resource being requested (default 1).
            skip_check: If True, bypass enforcement entirely.

        Raises:
            QuotaExceededException: If current_usage + delta > limit.

        Returns:
            None if the quota check passes.
        """
        async with self.uow as uow:
            plan_repo = uow.get_repository(IPlanRepository)
            subscription_repo = uow.get_repository(ISubscriptionRepository)

            if skip_check:
                return

            subscription = await subscription_repo.get_current_by_tenant(tenant_id)
            if subscription is None:
                raise ValueError(f"No existe una suscripción para el tenant {tenant_id}")

            plan = await plan_repo.get_by_id(subscription.plan_id)
            if plan is None:
                raise ValueError(f"No existe el plan {subscription.plan_id}")

            # Find matching quota by resource name
            quota = next((q for q in plan.quotas if q.name == resource), None)
            if quota is None:
                # No quota defined for this resource — allow
                return

            # Unlimited quota (-1) never blocks
            if quota.limit == -1:
                return

            # Get current usage from subscription metadata
            metadata = subscription.metadata or {}
            current_usage = int(metadata.get(resource, 0))

            if current_usage + delta > quota.limit:
                raise QuotaExceededException(
                    resource_name=resource,
                    limit=quota.limit,
                    current_usage=current_usage,
                )
