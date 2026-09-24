"""Application handler for MercadoPago authorized-payment notifications."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

from loguru import logger

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.events.payment_events import PaymentFailed, PaymentReceived
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    ISubscriptionRepository,
)
from src.common.application.ports.uow import IUoW, IUoWFactory
from src.common.domain.ports.event_bus import IEventBus


class SubscriptionAuthorizedPaymentHandler:
    """Process a MercadoPago subscription authorized-payment notification."""

    def __init__(
        self,
        gateway: IPaymentGateway,
        uow_factory: IUoWFactory,
        build_event_bus: Callable[[IUoW], IEventBus],
    ) -> None:
        self._gateway = gateway
        self._uow_factory = uow_factory
        self._build_event_bus = build_event_bus

    async def handle(self, authorized_payment_id: str) -> None:
        """Fetch, persist, and dispatch events for an authorized payment."""
        async with self._uow_factory() as uow:
            payment_repo = uow.get_repository(IPaymentRepository)
            sub_repo = uow.get_repository(ISubscriptionRepository)

            # Fetch authorized payment from MP
            auth = await self._gateway.get_authorized_payment(authorized_payment_id)
            mp_payment_id = auth.payment_id or authorized_payment_id

            # Idempotency: check if this mp_payment_id was already recorded
            existing = await payment_repo.get_by_mp_payment_id(mp_payment_id)
            if existing is not None:
                return

            amount = auth.transaction_amount or Decimal("0.00")

            # Find subscription by gateway subscription id from the auth payment
            # AuthorizedPaymentResult now carries preapproval_id
            local_sub = await sub_repo.get_by_gateway_subscription_id(auth.preapproval_id)
            if local_sub is None:
                logger.warning(
                    "subscription_authorized_payment — no local sub for authorized_payment={}",
                    authorized_payment_id,
                )
                return

            # Create payment record
            payment = Payment(
                tenant_id=local_sub.tenant_id,
                subscription_id=local_sub.id,
                status=PaymentStatus.APPROVED if auth.status == "approved" else PaymentStatus.REJECTED,
                amount=amount,
                mp_payment_id=mp_payment_id,
                paid_at=(datetime.now(tz=timezone.utc) if auth.status == "approved" else None),
                description="Subscription charge",
            )
            await payment_repo.create(payment)

            if auth.status == "approved":
                # Update subscription dates
                updated = replace(
                    local_sub,
                    status=SubscriptionStatus.ACTIVE,
                    next_billing_date=auth.next_billing_date or local_sub.next_billing_date,
                )
                await sub_repo.update(updated)

                # Emit PaymentReceived
                bus = self._build_event_bus(uow)
                event = PaymentReceived(
                    aggregate_id=payment.id,
                    payment_id=payment.id,
                    amount=amount,
                    currency="ARS",
                    tenant_id=local_sub.tenant_id,
                    next_billing_date=auth.next_billing_date,
                )
                await bus.dispatch(event)

            elif auth.status == "rejected":
                # MP has exhausted retries — set PAST_DUE
                updated = replace(
                    local_sub,
                    status=SubscriptionStatus.PAST_DUE,
                )
                await sub_repo.update(updated)

                # Emit PaymentFailed
                bus = self._build_event_bus(uow)
                event = PaymentFailed(
                    aggregate_id=payment.id,
                    payment_id=payment.id,
                    tenant_id=local_sub.tenant_id,
                    subscription_id=local_sub.id,
                    amount=amount,
                    failure_reason="MP retry exhaustion",
                )
                await bus.dispatch(event)

            await uow.commit()
