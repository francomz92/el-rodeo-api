"""Handler that queues any dispatched domain event into the UoW outbox.

Register this handler for every event type so that events dispatched
through the bus are persisted to the ``event_outbox`` table during the
next UoW commit.
"""

from src.common.application.ports.uow import IUoW
from src.common.domain.events.base import DomainEvent


class OutboxScheduler:
    """Handler that queues a domain event into the UoW outbox.

    Usage::

        bus = InMemoryEventBus()
        uow = UnitOfWork(...)
        bus.register("*", OutboxScheduler(uow))
        bus.register("animal.created", OutboxScheduler(uow))
    """

    def __init__(self, uow: IUoW) -> None:
        self._uow = uow

    def __call__(self, event: DomainEvent) -> None:
        """Append *event* to the UoW outbox queue for transactional persistence."""
        self._uow.add_outbox_event(event)
