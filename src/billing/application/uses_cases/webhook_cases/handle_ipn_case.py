"""HandleIpnCase — processes MercadoPago IPN notifications.

Validates x-signature, then dispatches the notification to the matching
topic case. Each ``execute`` call creates its own ``UnitOfWork`` with a
fresh DB session (via the case handlers) so it can safely run as a
background task.

Signature validation FAILS OPEN when no webhook secret is configured:
with an empty ``webhook_secret`` both ``validate_signature`` and
``execute`` accept the notification without checking ``x-signature``.
This is deliberate (development and tests run without an MP secret) and
must not be relied on in production, where ``MP_WEBHOOK_SECRET`` has to
be set — documented per F2-5 map #19 (odd/tasks/billing-refactor.md);
the runtime behaviour is unchanged in this phase.
"""

from src.billing.application.ports.payment_event_bus_factory import (
    IPaymentEventBusFactory,
)
from src.billing.application.uses_cases.webhook_cases.handle_authorized_payment_case import (
    HandleAuthorizedPaymentCase,
)
from src.billing.application.uses_cases.webhook_cases.handle_payment_notification_case import (
    HandlePaymentNotificationCase,
)
from src.billing.application.uses_cases.webhook_cases.handle_preapproval_case import (
    HandlePreapprovalCase,
)
from src.billing.domain.exceptions import PaymentGatewayError
from src.billing.domain.repositories import IPaymentGateway, IPlanRepository
from src.common.application.ports.uow import IUoW, IUoWFactory
from src.common.domain.ports.event_bus import IEventBus
from src.common.utils import log


class HandleIpnCase:
    """Process MercadoPago IPN webhook notifications.

    Validates x-signature, fetches payment details from MP, persists
    the payment record with idempotency, and transitions the associated
    subscription. On APPROVED, emits a ``PaymentReceived`` domain event.

    Each ``execute`` call creates its own ``UnitOfWork`` with a fresh
    DB session so it can safely run as a background task.

    Security note (fail-open, F2-5 map #19): when ``webhook_secret`` is
    empty the x-signature check is SKIPPED entirely — requests are
    accepted unverified. Configuring ``MP_WEBHOOK_SECRET`` is what turns
    validation on; the behaviour is intentionally unchanged in this phase.
    """

    def __init__(
        self,
        gateway: IPaymentGateway,
        plan_repo: IPlanRepository,
        uow_factory: IUoWFactory,
        event_bus_factory: IPaymentEventBusFactory,
        webhook_secret: str,
    ) -> None:
        self.gateway = gateway
        self.webhook_secret = webhook_secret
        self.plan_repo = plan_repo
        self.uow_factory = uow_factory
        self.event_bus_factory = event_bus_factory
        self._handle_preapproval_case = HandlePreapprovalCase(
            gateway=self.gateway,
            uow_factory=self.uow_factory,
        )
        self._handle_payment_notification_case = HandlePaymentNotificationCase(
            gateway=self.gateway,
            plan_repo=self.plan_repo,
            uow_factory=self.uow_factory,
            build_event_bus=self._build_event_bus,
        )
        self._handle_authorized_payment_case = HandleAuthorizedPaymentCase(
            gateway=self.gateway,
            uow_factory=self.uow_factory,
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

        Fail-open (F2-5 map #19): when the configured webhook secret is
        empty this returns ``True`` without inspecting the signature at
        all — an unset ``MP_WEBHOOK_SECRET`` disables verification.
        """
        secret = self.webhook_secret
        if not secret:
            return True
        return self.gateway.validate_signature(
            x_signature=x_signature,
            x_request_id=x_request_id,
            data_id=data_id,
            secret=secret,
        )

    async def execute(
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

        Security note (fail-open, F2-5 map #19): the x-signature is only
        verified when ``webhook_secret`` is non-empty; with an empty secret
        the check is skipped and the notification is processed unverified.
        """
        secret = self.webhook_secret
        if secret:
            valid = self.gateway.validate_signature(
                x_signature=x_signature,
                x_request_id=x_request_id,
                data_id=id,
                secret=secret,
            )
            if not valid:
                raise PaymentGatewayError(
                    message="Firma x-signature del webhook no válida",
                    status_code=401,
                )

        if topic == "payment":
            await self._handle_payment_notification_case.execute(id)
        elif topic == "merchant_order":
            pass
        elif topic == "subscription_preapproval":
            await self._handle_preapproval_case.execute(id)
        elif topic == "subscription_authorized_payment":
            await self._handle_authorized_payment_case.execute(id)
        else:
            log.warning("Unsupported IPN topic ignored: {}", topic)

    def _build_event_bus(self, uow: IUoW) -> IEventBus:
        """Build the event bus for *uow* through the configured factory."""
        return self.event_bus_factory.build(uow)
