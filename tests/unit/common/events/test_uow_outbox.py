"""Unit tests for IUoW outbox event integration."""

from uuid import UUID

from tests.mocks import MockUoW

from src.common.domain.events.base import DomainEvent


class TestIUoWOutboxContract:
    """IUoW must expose outbox_events and add_outbox_event()."""

    def test_outbox_events_defaults_to_empty_list(self) -> None:
        """IUoW.outbox_events is a dataclass field defaulting to empty list."""
        uow = MockUoW()
        assert uow.outbox_events == []

    def test_add_outbox_event_appends_to_list(self) -> None:
        """add_outbox_event() appends the domain event to outbox_events."""
        uow = MockUoW()
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        uow.add_outbox_event(event)

        assert len(uow.outbox_events) == 1
        assert uow.outbox_events[0] is event

    def test_add_outbox_event_multiple_events(self) -> None:
        """Multiple events accumulate in outbox_events."""
        uow = MockUoW()
        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.a",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="test.b",
        )

        uow.add_outbox_event(event_a)
        uow.add_outbox_event(event_b)

        assert len(uow.outbox_events) == 2
        assert uow.outbox_events[0] is event_a
        assert uow.outbox_events[1] is event_b

    def test_outbox_events_is_independent_per_uow_instance(self) -> None:
        """Each UoW instance has its own outbox_events list."""
        uow_a = MockUoW()
        uow_b = MockUoW()

        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        uow_a.add_outbox_event(event)

        assert len(uow_a.outbox_events) == 1
        assert len(uow_b.outbox_events) == 0


class TestMockUoWOutboxIntegration:
    """MockUoW stores and retrieves outbox events correctly."""

    def test_outbox_events_persisted_across_add_and_read(self) -> None:
        """Events added via add_outbox_event are present on the same instance."""
        uow = MockUoW()
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        uow.add_outbox_event(event)

        # Read back
        assert uow.outbox_events[0].event_id == event.event_id
        assert uow.outbox_events[0].event_type == "test.event"
