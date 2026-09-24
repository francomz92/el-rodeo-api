from typing import Protocol

from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class IPaymentEventBusFactory(Protocol):
    """Build payment event buses using the caller's active unit of work."""

    def build(self, uow: IUoW) -> IEventBus:
        """Build the event bus with handlers bound to ``uow``."""
        ...
