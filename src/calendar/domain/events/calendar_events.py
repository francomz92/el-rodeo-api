"""Animal domain events."""

from uuid import UUID

from src.common.domain.events.base import DomainEvent


class CalendarEventCreated(DomainEvent):
    """Emitted when a Calendar event is created."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="calendar_event.created",
            aggregate_id=aggregate_id,
            **kwargs,
        )


class CalendarEventUpdated(DomainEvent):
    """Emitted when a Calendar event is updated."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="calendar_event.updated",
            aggregate_id=aggregate_id,
            **kwargs,
        )


class CalendarEventDeleted(DomainEvent):
    """Emitted when a Calendar event is deleted."""

    def __init__(
        self,
        aggregate_id: UUID,
        **kwargs,
    ) -> None:
        super().__init__(
            event_type="calendar_event.deleted",
            aggregate_id=aggregate_id,
            **kwargs,
        )
