"""Event bus port (interface).

Defines the contract for synchronous event dispatch used by domain
use cases. Implementations handle handler registration and dispatch.
"""

from abc import ABC, abstractmethod
from collections.abc import Callable

from src.common.domain.events.base import DomainEvent


class IEventBus(ABC):
    """Port for a synchronous event bus.

    Provides ``register()`` to attach handlers to event types and
    ``dispatch()`` to notify all handlers for a given event.
    """

    @abstractmethod
    def register(
        self,
        event_type: str,
        handler: Callable[[DomainEvent], None],
    ) -> None:
        """Register *handler* to be called when *event_type* is dispatched.

        Multiple handlers can be registered for the same event type.
        They are invoked in registration order.
        """
        ...

    @abstractmethod
    def dispatch(self, event: DomainEvent) -> None:
        """Dispatch *event* to all registered handlers for its event type.

        Exceptions raised by individual handlers MUST NOT prevent other
        handlers from executing.  If no handlers are registered, this is
        a no-op.
        """
        ...
