"""Event bus port (interface).

Defines the contract for event dispatch used by domain use cases.
Implementations handle handler registration and dispatch, supporting both
sync and async handlers.
"""

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

from src.common.domain.events.base import DomainEvent

# A handler can be sync (returns None) or async (returns Awaitable).
Handler = Callable[[DomainEvent], Awaitable[None] | None]


class IEventBus(ABC):
    """Port for an event bus.

    Provides ``register()`` to attach handlers to event types and
    ``dispatch()`` to notify all handlers for a given event.
    """

    @abstractmethod
    def register(
        self,
        event_type: str,
        handler: Handler,
    ) -> None:
        """Register *handler* to be called when *event_type* is dispatched.

        Multiple handlers can be registered for the same event type.
        They are invoked in registration order.
        """
        ...

    @abstractmethod
    async def dispatch(self, event: DomainEvent) -> None:
        """Dispatch *event* to all registered handlers for its event type.

        Exceptions raised by individual handlers MUST NOT prevent other
        handlers from executing.  If no handlers are registered, this is
        a no-op.
        """
        ...
