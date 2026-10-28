"""GetSubscriptionCase — fetch one subscription with tenant isolation."""

from uuid import UUID

from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.repositories import ISubscriptionRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError


class GetSubscriptionCase:
    """Use case for fetching a single subscription of the requesting tenant."""

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
    ) -> SubscriptionEntity:
        """Return the subscription or raise NotFoundError (tenant-isolated)."""
        async with self.uow as uow:
            sub_repo = uow.get_repository(ISubscriptionRepository)
            subscription = await sub_repo.get_by_id(subscription_id)
            if subscription is None or subscription.tenant_id != tenant_id:
                raise NotFoundError("No existe la suscripción")
            return subscription
