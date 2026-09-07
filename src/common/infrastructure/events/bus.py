"""In-memory event bus implementation.

Provides a dict-backed event bus that stores handlers per event type and
dispatches events to all matching handlers in registration order.  Both
sync and async handlers are supported — the bus inspects the return value
and awaits it when it is a coroutine.

Handler exceptions are caught individually so a failing handler does not
block other handlers for the same event.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.event_bus import IEventBus
from src.common.utils import log


class InMemoryEventBus(IEventBus):
    """Dict-backed event bus that supports sync and async handlers.

    Handlers are stored per *event_type* and invoked in registration
    order during ``dispatch()``.  If a handler returns an awaitable, the
    bus awaits it before moving to the next handler.

    Usage::

        bus = InMemoryEventBus()
        bus.register("animal.created", my_handler)
        bus.register("animal.created", another_handler)
        await bus.dispatch(AnimalCreated(aggregate_id=some_uuid))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[DomainEvent], Awaitable[None] | None]]] = {}

    def register(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], Awaitable[None] | None],
    ) -> None:
        """Register a handler for a given event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch *event* to all registered handlers.

        Sync handlers are called directly; async handlers are awaited.
        If a handler raises, the exception is logged and remaining
        handlers continue execution.

        Handlers registered for ``"*"`` are invoked for every event type.
        """
        # Exact-match handlers first, then wildcard ``"*"`` handlers.
        handlers = list(self._handlers.get(event.event_type, []))
        handlers.extend(self._handlers.get("*", []))
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                log.exception(
                    "Handler {} failed for event {}",
                    handler.__name__,
                    event.event_id,
                )
