"""CancelSubscriptionCase — cancels an MP subscription."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID

from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.repositories import (
    IPaymentGateway,
    ISubscriptionRepository,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotFoundError


class CancelSubscriptionCase:
    """Use case that cancels an MP subscription.

    Finds the subscription, validates it belongs to the tenant, and:
    - If already CANCELED: no-op (idempotent)
    - Otherwise: calls gateway.cancel_subscription() and updates local status
    """

    def __init__(
        self,
        uow: IUoW,
        gateway: IPaymentGateway,
    ) -> None:
        self.uow = uow
        self.gateway = gateway

    async def execute(
        self,
        subscription_id: UUID,
        tenant_id: UUID,
    ) -> SubscriptionEntity:
        """Cancel an MP subscription.

        Args:
            subscription_id: The local subscription UUID.
            tenant_id: The tenant requesting cancellation.

        Returns:
            The updated SubscriptionEntity entity with status=CANCELED.

        Raises:
            NotFoundError: If the subscription does not exist or belongs to
                another tenant.
        """
        async with self.uow as uow:
            subscription_repo = uow.get_repository(ISubscriptionRepository)

            subscription = await subscription_repo.get_by_id(subscription_id)
            if subscription is None or subscription.tenant_id != tenant_id:
                raise NotFoundError(f"No existe la suscripción {subscription_id}")

            # Idempotent: already cancelled
            if subscription.status == SubscriptionStatus.CANCELED:
                return subscription

            # Cancel in gateway
            if subscription.gateway_subscription_id:
                await self.gateway.cancel_subscription(subscription.gateway_subscription_id)

            # Update local
            now = datetime.now(tz=timezone.utc)
            updated = replace(
                subscription,
                status=SubscriptionStatus.CANCELED,
                canceled_at=now,
            )
            result = await subscription_repo.update(updated)
            await uow.commit()
            return result
