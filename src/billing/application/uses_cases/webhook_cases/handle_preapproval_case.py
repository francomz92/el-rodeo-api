"""HandlePreapprovalCase — sync local subscription from a gateway preapproval notification."""

from dataclasses import replace

from src.billing.domain.repositories import IPaymentGateway, ISubscriptionRepository
from src.common.application.ports.uow import IUoWFactory
from src.common.utils import log


class HandlePreapprovalCase:
    """Sync local subscription state from a gateway preapproval notification."""

    def __init__(self, gateway: IPaymentGateway, uow_factory: IUoWFactory) -> None:
        self._gateway = gateway
        self._uow_factory = uow_factory

    async def execute(self, gateway_subscription_id: str) -> None:
        """Fetch gateway state and synchronize the matching local subscription."""
        async with self._uow_factory() as uow:
            sub_repo = uow.get_repository(ISubscriptionRepository)

            # Fetch subscription from gateway
            sub_result = await self._gateway.get_subscription(gateway_subscription_id)

            # Find local subscription
            local_sub = await sub_repo.get_by_gateway_subscription_id(gateway_subscription_id)
            if local_sub is None:
                log.warning(
                    "subscription_preapproval — no local subscription found for gateway_subscription_id={}",
                    gateway_subscription_id,
                )
                return

            # Sync state from gateway
            mp_status = sub_result.subscription_status or local_sub.status
            updated = replace(
                local_sub,
                gateway_subscription_id=sub_result.id,
                status=mp_status,
                current_period_end=sub_result.next_billing_date or local_sub.current_period_end,
                next_billing_date=sub_result.next_billing_date or local_sub.next_billing_date,
                billing_date=sub_result.billing_date or local_sub.billing_date,
                gateway_card_id=sub_result.card_id or local_sub.gateway_card_id,
            )
            await sub_repo.update(updated)
            await uow.commit()
