"""Webhook handler for MercadoPago IPN notifications."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from loguru import logger

from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.billing.application.events._payment_failed_email_handler import (
    PaymentFailedEmailHandler,
)
from src.billing.application.events.payment_confirmation_email_handler import (
    PaymentConfirmationEmailHandler,
)
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
from src.billing.infrastructure.payment_gateway._mappers import (
    map_mp_subscription_status,
)
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.application.ports.uow import IUoWFactory
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.core._config import settings
from src.common.infrastructure.events.bus import InMemoryEventBus
from src.common.infrastructure.events.handlers.outbox_scheduler import OutboxScheduler


class PaymentWebhookService:
    """Process MercadoPago IPN webhook notifications.

    Validates x-signature, fetches payment details from MP, persists
    the payment record with idempotency, and transitions the associated
    subscription. On APPROVED, emits a ``PaymentReceived`` domain event.

    Each ``handle_ipn`` call creates its own ``UnitOfWork`` with a fresh
    DB session so it can safely run as a background task.
    """

    def __init__(
        self,
        gateway: IPaymentGateway,
        plan_repo: IPlanRepository,
        uow_factory: IUoWFactory,
        email_notifier: IEmailNotifier,
    ) -> None:
        self._gateway = gateway
        self._plan_repo = plan_repo
        self._uow_factory = uow_factory
        self._email_notifier = email_notifier

    def validate_signature(
        self,
        x_signature: str,
        x_request_id: str,
        data_id: str,
    ) -> bool:
        """Synchronously validate a MercadoPago x-signature.

        Returns ``True`` if valid, ``False`` otherwise.
        Intended for use by the webhook router **before** spawning
        the async background task (defence in depth).
        """
        secret = settings.MP_WEBHOOK_SECRET
        if not secret:
            return True
        return self._gateway.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret=secret,
        )

    async def handle_ipn(
        self,
        topic: str,
        id: str,
        x_signature: str,
        x_request_id: str,
    ) -> None:
        """Process an IPN notification from MercadoPago.

        Creates its own ``UnitOfWork`` with a fresh DB session so the
        method can safely be run as a background task (outside the
        FastAPI request lifecycle).

        Args:
            topic: The notification topic (e.g. "payment").
            id: The resource ID from MP.
            x_signature: The x-signature header for validation.
            x_request_id: The x-request-id header for validation.

        Raises:
            PaymentGatewayError: If x-signature validation fails or the
                tenant/subscription cannot be resolved.
        """
        secret = settings.MP_WEBHOOK_SECRET
        if secret:
            valid = self._gateway.validate_signature(
                x_signature=x_signature,
                x_request_id=x_request_id,
                data_id=id,
                secret=secret,
            )
            if not valid:
                raise PaymentGatewayError(
                    message="Invalid webhook x-signature",
                    status_code=401,
                )

        if topic == "payment":
            await self._handle_payment_notification(id)
        elif topic == "merchant_order":
            pass
        elif topic == "subscription_preapproval":
            await self._handle_subscription_preapproval(id)
        elif topic == "subscription_authorized_payment":
            await self._handle_subscription_authorized_payment(id)
        else:
            logger.warning("Unsupported IPN topic ignored: {}", topic)

    async def _handle_payment_notification(self, payment_id: str) -> None:
        """Process a payment notification from MP with a fresh session context."""
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

    # ── Subscription webhook handlers (Phase 0b) ───────────────────────────

    async def _handle_subscription_preapproval(self, gateway_subscription_id: str) -> None:
        """Handle a subscription_preapproval webhook notification.

        Fetches the subscription from the gateway, finds the local subscription by
        gateway_subscription_id, and syncs status and billing dates.
        """
        async with self._uow_factory() as uow:
            sub_repo = uow.get_repository(ISubscriptionRepository)

            # Fetch subscription from gateway
            sub_result = await self._gateway.get_subscription(gateway_subscription_id)

            # Find local subscription
            local_sub = await sub_repo.get_by_gateway_subscription_id(gateway_subscription_id)
            if local_sub is None:
                logger.warning(
                    "subscription_preapproval — no local subscription found for gateway_subscription_id={}",
                    gateway_subscription_id,
                )
                await uow.commit()
                return

            # Sync state from gateway
            mp_status = map_mp_subscription_status(sub_result.status)
            datetime.now(tz=timezone.utc)
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

    async def _handle_subscription_authorized_payment(self, authorized_payment_id: str) -> None:
        """Handle a subscription_authorized_payment webhook notification.

        Fetches the authorized payment from MP, creates a Payment record
        with idempotency via mp_payment_id, updates the subscription
        billing dates, and emits PaymentReceived/PAST_DUE events.
        """
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

    def _build_event_bus(self, uow) -> IEventBus:
        """Build an event bus with handlers wired to *uow* repos.

        All handlers share the same UoW session so they can safely
        read/write within the current transaction.
        """
        bus = InMemoryEventBus()
        bus.register("*", OutboxScheduler(uow))

        user_repo = uow.get_repository(IUserRepository)
        email_handler = PaymentConfirmationEmailHandler(
            user_repo=user_repo,
            email_notifier=self._email_notifier,
        )
        bus.register("payment.received", email_handler)

        failed_email_handler = PaymentFailedEmailHandler(
            user_repo=user_repo,
            email_notifier=self._email_notifier,
        )
        bus.register("payment.failed", failed_email_handler)
        return bus
