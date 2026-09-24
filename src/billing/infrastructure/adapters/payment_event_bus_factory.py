from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.billing.application.events._payment_failed_email_handler import (
    PaymentFailedEmailHandler,
)
from src.billing.application.events.payment_confirmation_email_handler import (
    PaymentConfirmationEmailHandler,
)
from src.billing.application.ports.payment_event_bus_factory import (
    IPaymentEventBusFactory,
)
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.events.bus import InMemoryEventBus
from src.common.infrastructure.events.handlers.outbox_scheduler import OutboxScheduler


class PaymentEventBusFactory(IPaymentEventBusFactory):
    """Build payment event buses wired to the active unit of work."""

    def __init__(self, email_notifier: IEmailNotifier) -> None:
        self._email_notifier = email_notifier

    def build(self, uow: IUoW) -> IEventBus:
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
