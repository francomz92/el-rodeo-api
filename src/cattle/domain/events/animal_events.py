"""Animal domain events."""

from uuid import UUID

from src.common.domain.events.base import DomainEvent


class AnimalCreated(DomainEvent):
    """Emitted when a new animal is registered in the system."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="animal.created",
            aggregate_id=aggregate_id,
            **kwargs,
        )
