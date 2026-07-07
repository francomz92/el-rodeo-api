"""In-memory event bus implementation.

Provides a dict-backed, synchronous event bus that stores handlers per
event type and dispatches events to all matching handlers in registration
order.  Handler exceptions are caught individually so a failing handler
does not block other handlers for the same event.
"""

from collections.abc import Callable
from logging import getLogger

from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.event_bus import IEventBus

logger = getLogger(__name__)


class InMemoryEventBus(IEventBus):
    """Dict-backed synchronous event bus.

    Handlers are stored per *event_type* and invoked in registration
    order during ``dispatch()``.  Handler exceptions are logged and
    isolated — one failing handler never blocks others.

    Usage::

        bus = InMemoryEventBus()
        bus.register("animal.created", my_handler)
        bus.register("animal.created", another_handler)
        bus.dispatch(AnimalCreated(aggregate_id=some_uuid))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[DomainEvent], None]]] = {}

    def register(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """Register a handler for a given event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, event: DomainEvent) -> None:
        """Dispatch an event to all registered handlers.

        Each handler is called in registration order.  If a handler
        raises, the exception is logged and other handlers continue
        execution.
        """
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Handler %s failed for event %s",
                    handler.__name__,
                    event.event_id,
                )
