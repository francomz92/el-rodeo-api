"""PaymentFailedEmailHandler — sends dunning notification emails.

Receives a ``PaymentFailed`` domain event for a REJECTED/CANCELLED/
REFUNDED/CHARGED_BACK payment and sends a dunning notification email
to all ADMIN and OWNER users of the tenant.

The handler queries ADMIN and OWNER users separately (the repository
only accepts a single role), deduplicates by user ID, and sends one
email per unique user.  Exceptions are caught and logged so the event
bus dispatch never crashes.
"""

from datetime import datetime, timezone

from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.billing.domain.events.payment_events import PaymentFailed
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.utils import log


class PaymentFailedEmailHandler:
    """Send a dunning notification email when a payment fails.

    Resolves ADMIN and OWNER users via ``IUserRepository`` (two calls,
    deduped by user ID) and delegates email delivery to
    ``IEmailNotifier`` (which dispatches through Celery with retry).
    Exceptions are caught and logged so dispatch never crashes.
    """

    def __init__(
        self,
        user_repo: IUserRepository,
        email_notifier: IEmailNotifier,
    ) -> None:
        self._user_repo = user_repo
        self._email_notifier = email_notifier

    async def __call__(self, event: PaymentFailed) -> None:
        """Handle a PaymentFailed event.

        Queries ADMIN and OWNER users, deduplicates by ID, and sends
        a dunning email to each unique user.  All exceptions are caught
        and logged.
        """
        tenant_id = getattr(event, "tenant_id", None)
        if tenant_id is None:
            return

        # Collect recipients from both ADMIN and OWNER roles
        seen_user_ids: set = set()
        recipients: list = []

        for role in (UserRole.ADMIN, UserRole.OWNER):
            page = 1
            while True:
                users, _total, has_next = await self._user_repo.list(
                    tenant_id=tenant_id,
                    role=role,
                    per_page=50,
                    page=page,
                )
                for user in users:
                    if user.id not in seen_user_ids:
                        seen_user_ids.add(user.id)
                        recipients.append(user)
                if not has_next:
                    break
                page += 1

        if not recipients:
            log.warning(
                "No ADMIN or OWNER users found for tenant {}, skipping dunning email",
                tenant_id,
            )
            return

        amount = getattr(event, "amount", None)
        failure_reason = getattr(event, "failure_reason", None)
        occurred_at = getattr(event, "occurred_at", datetime.now(timezone.utc))
        payment_id = getattr(event, "payment_id", "unknown")

        date_str = occurred_at.strftime("%d/%m/%Y") if isinstance(occurred_at, datetime) else str(occurred_at)
        amount_str = f"${amount}" if amount is not None else "N/A"
        reason_str = f"Motivo: {failure_reason}.\n" if failure_reason else ""

        subject = "Pago rechazado — El Rodeo"

        for recipient in recipients:
            body = (
                f"Hola {recipient.name},\n\n"
                f"El pago de tu suscripción en El Rodeo fue rechazado.\n\n"
                f"Detalle:\n"
                f"- Monto: {amount_str}\n"
                f"- Fecha: {date_str}\n"
                f"{reason_str}"
                f"- Estado de la suscripción: PAST_DUE (vencida)\n\n"
                f"Tu suscripción se encuentra PAST_DUE. Para evitar la interrupción del servicio, "
                f"por favor actualizá tu método de pago ingresando a la aplicación.\n\n"
                f"Podés actualizar tu método de pago en:\n"
                f"https://app.elrodeo.com/configuracion/pago\n\n"
                f"Si ya realizaste el pago, por favor ignorá este mensaje.\n\n"
                f"El equipo de El Rodeo"
            )

            try:
                self._email_notifier.send(
                    to=[recipient.email],
                    subject=subject,
                    body=body,
                )
            except Exception:
                log.exception(
                    "Failed to send dunning email for payment {} to {}",
                    payment_id,
                    recipient.email,
                )
