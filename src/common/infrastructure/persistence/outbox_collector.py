"""Collect and persist domain events within the active database transaction."""

import dataclasses
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.persistence.models.event_outbox import EventOutbox


def serialize_event(event: DomainEvent) -> dict:
    """Serialize a domain event to a JSON-safe dict including subclass fields."""
    raw = dataclasses.asdict(event)
    return {key: str(value) if isinstance(value, (UUID, datetime)) else value for key, value in raw.items()}


class OutboxCollector:
    """Manage queued domain events and serialize them for the active session."""

    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    def add_event(self, event: DomainEvent) -> None:
        """Append *event* to the FIFO queue without copying it."""
        self.events.append(event)

    def flush(self, session: AsyncSession) -> None:
        """Serialize queued events and add rows to the active transaction."""
        for event in self.events:
            session.add(
                EventOutbox(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    aggregate_id=event.aggregate_id,
                    payload=serialize_event(event),
                )
            )
        self.clear()

    def clear(self) -> None:
        """Clear the existing queue in place."""
        self.events.clear()
