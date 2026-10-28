"""PaymentConfirmationEmailHandler — sends payment confirmation emails.

Receives a ``PaymentReceived`` domain event for an APPROVED payment and
sends a confirmation email to the tenant owner via ``IEmailNotifier``.
"""

from datetime import datetime, timezone

from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.domain.events.base import DomainEvent
from src.common.utils import log


class PaymentConfirmationEmailHandler:
    """Send a confirmation email when a payment is received and approved.

    Resolves the tenant owner via ``IUserRepository`` and delegates email
    delivery to ``IEmailNotifier`` (which dispatches through Celery).
    Exceptions are caught and logged so dispatch never crashes.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        email_notifier: IEmailNotifier,
    ) -> None:
        self._user_repo = user_repo
        self._email_notifier = email_notifier

    async def __call__(self, event: DomainEvent) -> None:
        """Handle a PaymentReceived event.

        Resolves the tenant owner via IUserRepository and sends a
        confirmation email.  Catches all exceptions so the event bus
        dispatch never crashes.
        """
        tenant_id = getattr(event, "tenant_id", None)
        if tenant_id is None:
            return

        # Resolve tenant owner via repository
        owners, _total, _has_next = await self._user_repo.list(
            tenant_id=tenant_id,
            role=UserRole.OWNER,
            per_page=1,
        )
        if not owners:
            log.warning(
                "Owner not found for tenant {}, skipping confirmation email",
                tenant_id,
            )
            return

        owner = owners[0]
        amount = getattr(event, "amount", None)
        payment_date = getattr(event, "timestamp", datetime.now(timezone.utc))
        plan_type = getattr(event, "plan_type", "N/A")
        next_billing = getattr(event, "next_billing_date", None)
        payment_id = getattr(event, "payment_id", "unknown")

        next_billing_str = next_billing.strftime("%d/%m/%Y") if next_billing else "N/A"
        invoice_link = f"https://app.elrodeo.com/facturas/{payment_id}"

        body = (
            f"Hola {owner.name},\n\n"
            f"Tu pago de ${amount} fue procesado exitosamente.\n\n"
            f"Detalle:\n"
            f"- Monto: ${amount}\n"
            f"- Fecha: {payment_date.strftime('%d/%m/%Y')}\n"
            f"- Plan: {plan_type}\n"
            f"- Próxima facturación: {next_billing_str}\n\n"
            f"Podés ver tu factura en: {invoice_link}\n\n"
            f"Gracias por confiar en El Rodeo.\n"
            f"El equipo de El Rodeo"
        )

        try:
            self._email_notifier.send(
                to=[owner.email],
                subject="Pago confirmado - El Rodeo",
                body=body,
            )
        except Exception:
            log.exception(
                "Failed to send confirmation email for payment {}",
                payment_id,
            )
