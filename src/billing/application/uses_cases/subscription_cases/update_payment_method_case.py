"""UpdatePaymentMethodCase — updates the card on an MP subscription."""

from dataclasses import replace
from uuid import UUID

from src.billing.domain.entities.subscriptions import SubscriptionEntity
from src.billing.domain.repositories import (
    IPaymentGateway,
    ISubscriptionRepository,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import BusinessValidationError, NotFoundError


class UpdatePaymentMethodCase:
    """Use case that updates the payment method (card) for an MP subscription."""

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
        card_token_id: str,
    ) -> SubscriptionEntity:
        """Update the payment method (card) for an MP subscription.

        Args:
            subscription_id: The local subscription UUID.
            tenant_id: The tenant requesting the update.
            card_token_id: The new card token from MercadoPago.js CardForm.

        Returns:
            The updated SubscriptionEntity entity with new gateway_card_id.

        Raises:
            NotFoundError: If the subscription does not exist or belongs to
                another tenant.
        """
        async with self.uow as uow:
            subscription_repo = uow.get_repository(ISubscriptionRepository)

            subscription = await subscription_repo.get_by_id(subscription_id)
            if subscription is None or subscription.tenant_id != tenant_id:
                raise NotFoundError(f"No existe la suscripción {subscription_id}")

            # Update in gateway
            if not subscription.gateway_subscription_id:
                raise BusinessValidationError(
                    "La suscripción no está gestionada por la pasarela de pago; no se puede actualizar su método de pago",
                )
            result = await self.gateway.update_subscription(
                subscription.gateway_subscription_id,
                {"card_token_id": card_token_id},
            )
            new_card_id = result.card_id

            # Update local
            updated = replace(
                subscription,
                gateway_card_id=new_card_id,
            )
            result_sub = await subscription_repo.update(updated)
            await uow.commit()
            return result_sub
