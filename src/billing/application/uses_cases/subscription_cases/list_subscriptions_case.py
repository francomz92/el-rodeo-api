"""ListSubscriptionsCase — list a tenant's subscriptions."""

from uuid import UUID

from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.repositories import ISubscriptionRepository
from src.common.application.ports.uow import IUoW


class ListSubscriptionsCase:
    """Use case for listing a tenant's subscriptions.

    All queries are scoped to the requesting tenant to enforce cross-tenant
    isolation.
    """

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        tenant_id: UUID,
        status_filter: SubscriptionStatus | None = None,
    ) -> list[SubscriptionEntity]:
        """Return the subscriptions of a tenant, optionally filtered by status."""
        async with self.uow as uow:
            sub_repo = uow.get_repository(ISubscriptionRepository)
            return await sub_repo.list_by_tenant(tenant_id, status_filter=status_filter)
