"""Webhook handler for MercadoPago IPN notifications."""

from loguru import logger

from src.billing.application.ports.payment_event_bus_factory import (
    IPaymentEventBusFactory,
)
from src.billing.application.services.payment_notification_handler import (
    PaymentNotificationHandler,
)
from src.billing.application.services.subscription_authorized_payment_handler import (
    SubscriptionAuthorizedPaymentHandler,
)
from src.billing.application.services.subscription_preapproval_handler import (
    SubscriptionPreapprovalHandler,
)
from src.billing.domain.exceptions import PaymentGatewayError
from src.billing.domain.repositories import IPaymentGateway, IPlanRepository
from src.common.application.ports.uow import IUoW, IUoWFactory
from src.common.domain.ports.event_bus import IEventBus


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
        event_bus_factory: IPaymentEventBusFactory,
        webhook_secret: str,
    ) -> None:
        self._gateway = gateway
        self._webhook_secret = webhook_secret
        self._plan_repo = plan_repo
        self._uow_factory = uow_factory
        self._event_bus_factory = event_bus_factory
        self._subscription_preapproval_handler = SubscriptionPreapprovalHandler(
            gateway=self._gateway,
            uow_factory=self._uow_factory,
        )
        self._payment_notification_handler = PaymentNotificationHandler(
            gateway=self._gateway,
            plan_repo=self._plan_repo,
            uow_factory=self._uow_factory,
            build_event_bus=self._build_event_bus,
        )
        self._subscription_authorized_payment_handler = SubscriptionAuthorizedPaymentHandler(
            gateway=self._gateway,
            uow_factory=self._uow_factory,
            build_event_bus=self._build_event_bus,
        )

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
        secret = self._webhook_secret
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
        secret = self._webhook_secret
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
        """Delegate payment notification handling to its application handler."""
        await self._payment_notification_handler.handle(payment_id)

    # ── Subscription webhook handlers (Phase 0b) ───────────────────────────

    async def _handle_subscription_preapproval(self, gateway_subscription_id: str) -> None:
        """Delegate subscription_preapproval handling to its application handler."""
        await self._subscription_preapproval_handler.handle(gateway_subscription_id)

    async def _handle_subscription_authorized_payment(self, authorized_payment_id: str) -> None:
        """Delegate subscription_authorized_payment handling to its application handler."""
        await self._subscription_authorized_payment_handler.handle(authorized_payment_id)

    def _build_event_bus(self, uow: IUoW) -> IEventBus:
        """Build the event bus for *uow* through the configured factory."""
        return self._event_bus_factory.build(uow)
