from typing import Annotated

from fastapi import Depends

from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.events.bus import InMemoryEventBus


def _get_event_bus() -> IEventBus:
    return InMemoryEventBus()


GetEventBus = Annotated[IEventBus, Depends(_get_event_bus)]
