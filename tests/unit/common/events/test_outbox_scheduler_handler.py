"""Unit tests for OutboxScheduler handler.

Verifies that calling the handler queues a domain event into the UoW
outbox_events collection.
"""

from uuid import UUID

from tests.mocks import MockUoW

from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.events.handlers.outbox_scheduler import OutboxScheduler


class TestOutboxScheduler:
    """OutboxScheduler queues dispatched events into the UoW outbox."""

    def setup_method(self) -> None:
        self.uow = MockUoW()
        self.handler = OutboxScheduler(uow=self.uow)

    def test_handler_adds_event_to_uow_outbox(self) -> None:
        """Calling the handler adds the event to uow.outbox_events."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        self.handler(event)

        assert len(self.uow.outbox_events) == 1
        assert self.uow.outbox_events[0] is event

    def test_handler_adds_multiple_events(self) -> None:
        """Multiple handler calls accumulate events in the outbox."""
        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.a",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="test.b",
        )

        self.handler(event_a)
        self.handler(event_b)

        assert len(self.uow.outbox_events) == 2
        assert self.uow.outbox_events == [event_a, event_b]

    def test_handler_is_callable(self) -> None:
        """OutboxScheduler is callable with a DomainEvent."""
        assert callable(self.handler)
