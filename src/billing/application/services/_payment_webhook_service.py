"""Webhook handler for MercadoPago IPN notifications."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from src.billing.domain.entities._payment import Payment
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.events.payment_events import PaymentReceived
from src.billing.domain.exceptions import MercadoPagoError
from src.billing.domain.repositories import (
    IPaymentGateway,
    IPaymentRepository,
    ISubscriptionRepository,
)
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.core._config import settings


class PaymentWebhookService:
    """Process MercadoPago IPN webhook notifications.

    Validates x-signature, fetches payment details from MP, persists
    the payment record with idempotency, and transitions the associated
    subscription. On APPROVED, emits a ``PaymentReceived`` domain event.
    """

    def __init__(
        self,
        gateway: IPaymentGateway,
        payment_repo: IPaymentRepository,
        subscription_repo: ISubscriptionRepository,
        event_bus: IEventBus,
    ) -> None:
        self._gateway = gateway
        self._payment_repo = payment_repo
        self._subscription_repo = subscription_repo
        self._event_bus = event_bus

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
            return True  # no secret configured — skip validation
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

        Args:
            topic: The notification topic (e.g. "payment").
            id: The resource ID from MP.
            x_signature: The x-signature header for validation.
            x_request_id: The x-request-id header for validation.

        Raises:
            ValueError: If topic is not supported.
            MercadoPagoError: If x-signature validation fails.
        """
        # Validate x-signature (required — always present after router-level check)
        secret = settings.MP_WEBHOOK_SECRET
        if secret:
            valid = self._gateway.validate_signature(
                x_signature=x_signature,
                x_request_id=x_request_id,
                data_id=id,
                secret=secret,
            )
            if not valid:
                raise MercadoPagoError(
                    message="Invalid webhook x-signature",
                    status_code=401,
                )

        if topic == "payment":
            await self._handle_payment_notification(id)
        elif topic == "merchant_order":
            # Merchant orders are not handled yet
            pass
        else:
            raise ValueError(f"Unsupported IPN topic: {topic}")

    async def _handle_payment_notification(self, payment_id: str) -> None:
        """Process a payment notification from MP.

        Resolves the tenant and subscription from external_reference,
        persists the payment, and transitions the subscription status.
        """
        # Idempotency: skip if payment already exists
        existing = await self._payment_repo.get_by_mp_payment_id(payment_id)
        if existing is not None:
            return

        # Fetch full payment details from MP
        payment_result = await self._gateway.get_payment(payment_id)

        # Resolve tenant_id and subscription_id from external_reference
        # Format: "{tenant_id}:{plan_type}"
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
            sub = await self._subscription_repo.get_by_tenant(tenant_id)
            if sub is not None:
                subscription_id = sub.id

        if tenant_id is None or subscription_id is None:
            raise MercadoPagoError(
                message=(f"Cannot resolve tenant/subscription for payment {payment_id}. external_reference={external_ref!r}"),
                status_code=400,
            )

        amount = payment_result.transaction_amount or Decimal("0.00")

        # Create payment record
        payment = Payment(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            status=payment_result.status,
            amount=amount,
            mp_payment_id=payment_id,
            mp_preference_id=None,
            paid_at=(datetime.now(tz=timezone.utc) if payment_result.status == PaymentStatus.APPROVED else None),
        )
        await self._payment_repo.create(payment)

        # Transition subscription based on payment status
        if payment_result.status == PaymentStatus.APPROVED:
            sub = await self._subscription_repo.get_by_id(subscription_id)
            if sub is not None:
                sub.status = SubscriptionStatus.ACTIVE  # type: ignore[attr-defined]
                sub.current_period_start = datetime.now(tz=timezone.utc)  # type: ignore[attr-defined]
                sub.current_period_end = datetime.now(tz=timezone.utc) + timedelta(days=30)  # type: ignore[attr-defined]
                sub.mp_preference_id = payment_result.id  # type: ignore[attr-defined]
                await self._subscription_repo.update(sub)

            # Emit PaymentReceived domain event
            payment_received = PaymentReceived(
                aggregate_id=payment.id,
                payment_id=payment.id,
                amount=amount,
                currency="ARS",
            )
            self._event_bus.dispatch(payment_received)

        elif payment_result.status in (
            PaymentStatus.REJECTED,
            PaymentStatus.CANCELLED,
            PaymentStatus.REFUNDED,
            PaymentStatus.CHARGED_BACK,
        ):
            sub = await self._subscription_repo.get_by_id(subscription_id)
            if sub is not None and sub.status == SubscriptionStatus.ACTIVE:
                sub.status = SubscriptionStatus.PAST_DUE  # type: ignore[attr-defined]
                await self._subscription_repo.update(sub)
