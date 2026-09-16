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


class AnimalUpdated(DomainEvent):
    """Emitted when an animal is updated."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="animal.updated",
            aggregate_id=aggregate_id,
            **kwargs,
        )


class AnimalDeleted(DomainEvent):
    """Emitted when an animal is deleted."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="animal.deleted",
            aggregate_id=aggregate_id,
            **kwargs,
        )


class AnimalProtocolCreated(DomainEvent):
    """Emitted when an animal protocol is created."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="animal_protocol.created",
            aggregate_id=aggregate_id,
            **kwargs,
        )


class AnimalProtocolUpdated(DomainEvent):
    """Emitted when an animal protocol is updated."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="animal_protocol.updated",
            aggregate_id=aggregate_id,
            **kwargs,
        )
