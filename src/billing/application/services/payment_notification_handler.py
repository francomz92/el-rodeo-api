"""Application handler for MercadoPago payment notifications."""

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from loguru import logger

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._plan_type import PlanTypeEntity
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.events.payment_events import PaymentFailed, PaymentReceived
from src.billing.domain.exceptions import PaymentGatewayError
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    IPlanRepository,
    ISubscriptionRepository,
)
from src.common.application.ports.uow import IUoW, IUoWFactory
from src.common.domain.ports.event_bus import IEventBus


class PaymentNotificationHandler:
    """Process a MercadoPago payment notification."""

    def __init__(
        self,
        gateway: IPaymentGateway,
        plan_repo: IPlanRepository,
        uow_factory: IUoWFactory,
        build_event_bus: Callable[[IUoW], IEventBus],
    ) -> None:
        self._gateway = gateway
        self._plan_repo = plan_repo
        self._uow_factory = uow_factory
        self._build_event_bus = build_event_bus

    async def handle(self, payment_id: str) -> None:
        """Fetch, persist, and dispatch events for a payment notification."""
        async with self._uow_factory() as uow:
            payment_repo = uow.get_repository(IPaymentRepository)
            sub_repo = uow.get_repository(ISubscriptionRepository)

            existing = await payment_repo.get_by_mp_payment_id(payment_id)
            if existing is not None:
                return

            payment_result = await self._gateway.get_payment(payment_id)

            tenant_id: UUID | None = None
            subscription_id: UUID | None = None

            external_ref = payment_result.external_reference
            if external_ref and ":" in external_ref:
                tenant_part = external_ref.split(":")[0]
                try:
                    tenant_id = UUID(tenant_part)
                except ValueError:
                    tenant_id = None

            if tenant_id is not None:
                sub = await sub_repo.get_by_tenant(tenant_id)
                if sub is not None:
                    subscription_id = sub.id

            if tenant_id is None or subscription_id is None:
                raise PaymentGatewayError(
                    message=(f"Cannot resolve tenant/subscription for payment {payment_id}. external_reference={external_ref!r}"),
                    status_code=400,
                )

            amount = payment_result.transaction_amount or Decimal("0.00")

            payment = Payment(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                status=payment_result.status,
                amount=amount,
                mp_payment_id=payment_id,
                mp_preference_id=None,
                paid_at=(datetime.now(tz=timezone.utc) if payment_result.status == PaymentStatus.APPROVED else None),
            )
            await payment_repo.create(payment)

            if payment_result.status == PaymentStatus.APPROVED:
                sub = await sub_repo.get_by_id(subscription_id)

                next_billing_date: datetime | None = None
                plan_type_str: str | None = None
                if sub is not None:
                    next_billing_date = sub.current_period_end
                    # Resolve plan_type from external_reference: "{tenant_id}:{plan_type}"
                    resolved_plan_id = sub.plan_id
                    if external_ref and ":" in external_ref:
                        candidate = external_ref.split(":")[-1]
                        try:
                            plan_enum = PlanTypeEntity(candidate)
                            plan = await self._plan_repo.get_by_plan_type(plan_enum)
                            if plan is not None:
                                resolved_plan_id = plan.id
                                plan_type_str = str(plan.plan_type)
                        except ValueError:
                            pass

                    now = datetime.now(tz=timezone.utc)
                    # Stores the last payment ID associated with this subscription
                    # (not a preference/checkout ID — gateway_preference_id is
                    # repurposed here for correlation)
                    updated = replace(
                        sub,
                        status=SubscriptionStatus.ACTIVE,
                        plan_id=resolved_plan_id,
                        current_period_start=now,
                        current_period_end=now + timedelta(days=30),
                        gateway_preference_id=payment_result.id,
                    )
                    await sub_repo.update(updated)

                bus = self._build_event_bus(uow)

                payment_received = PaymentReceived(
                    aggregate_id=payment.id,
                    payment_id=payment.id,
                    amount=amount,
                    currency="ARS",
                    tenant_id=tenant_id,
                    plan_type=plan_type_str,
                    next_billing_date=next_billing_date,
                )
                await bus.dispatch(payment_received)

            elif payment_result.status in (
                PaymentStatus.REJECTED,
                PaymentStatus.CANCELED,
                PaymentStatus.REFUNDED,
                PaymentStatus.CHARGED_BACK,
            ):
                sub = await sub_repo.get_by_id(subscription_id)

                # For MP-managed subscriptions, don't set PAST_DUE on individual
                # topic=payment rejections — MP manages its own retry cycle
                if sub is not None and sub.gateway_subscription_id is not None:
                    logger.info(
                        "payment rejection for MP-managed sub {} — deferring PAST_DUE to MP retry exhaustion",
                        sub.id,
                    )
                elif sub is not None and sub.status == SubscriptionStatus.ACTIVE:
                    updated = replace(
                        sub,
                        status=SubscriptionStatus.PAST_DUE,
                    )
                    await sub_repo.update(updated)

                    # Emit PaymentFailed event for legacy subs
                    plan_type_str_fail: str | None = None
                    if external_ref and ":" in external_ref:
                        candidate = external_ref.split(":")[-1]
                        try:
                            plan_type_str_fail = str(PlanTypeEntity(candidate))
                        except ValueError:
                            plan_type_str_fail = candidate

                    bus = self._build_event_bus(uow)
                    payment_failed = PaymentFailed(
                        aggregate_id=payment.id,
                        payment_id=payment.id,
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        plan_type=plan_type_str_fail,
                        amount=amount,
                        failure_reason=payment_result.status.value,
                    )
                    await bus.dispatch(payment_failed)

            await uow.commit()
