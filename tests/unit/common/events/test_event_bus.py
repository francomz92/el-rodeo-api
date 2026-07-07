"""Unit tests for IEventBus contract and InMemoryEventBus implementation."""

from uuid import UUID

import pytest

from src.common.domain.events.base import DomainEvent
from src.common.domain.ports.event_bus import IEventBus
from src.common.infrastructure.events.bus import InMemoryEventBus


class TestIEventBusContract:
    """IEventBus is an ABC — concrete classes must implement register and dispatch."""

    def test_cannot_instantiate_abc_directly(self) -> None:
        """IEventBus cannot be instantiated because it has abstract methods."""
        with pytest.raises(TypeError):
            IEventBus()  # type: ignore[abstract]

    def test_concrete_must_implement_register_and_dispatch(self) -> None:
        """A subclass missing register or dispatch raises TypeError."""
        with pytest.raises(TypeError):

            class BadBus(IEventBus):  # type: ignore[abstract]
                pass

            BadBus()


class TestInMemoryEventBus:
    """InMemoryEventBus dispatches events to registered handlers."""

    def setup_method(self) -> None:
        self.bus = InMemoryEventBus()

    def test_register_adds_handler_for_event_type(self) -> None:
        """After registering, the handler is stored for that event type."""
        calls: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            calls.append(event)

        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.bus.register("test.event", handler)
        self.bus.dispatch(event)

        assert len(calls) == 1
        assert calls[0] is event

    def test_dispatch_calls_all_handlers_for_event_type(self) -> None:
        """Multiple handlers for the same event type are all invoked."""
        results: list[str] = []

        def handler_a(event: DomainEvent) -> None:
            results.append("a")

        def handler_b(event: DomainEvent) -> None:
            results.append("b")

        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.bus.register("test.event", handler_a)
        self.bus.register("test.event", handler_b)
        self.bus.dispatch(event)

        assert results == ["a", "b"]

    def test_handler_exception_does_not_block_other_handlers(self) -> None:
        """When a handler raises, remaining handlers still execute."""
        results: list[str] = []

        def failing_handler(event: DomainEvent) -> None:
            msg = "oops"
            raise ValueError(msg)

        def good_handler(event: DomainEvent) -> None:
            results.append("ok")

        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.bus.register("test.event", failing_handler)
        self.bus.register("test.event", good_handler)
        self.bus.dispatch(event)

        assert results == ["ok"]

    def test_dispatch_does_not_call_handlers_for_other_types(self) -> None:
        """Handlers are only called for their registered event type."""
        calls: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            calls.append(event)

        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="type_a",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="type_b",
        )
        self.bus.register("type_a", handler)
        self.bus.dispatch(event_b)

        assert len(calls) == 0

    def test_dispatch_calls_handlers_in_registration_order(self) -> None:
        """Handlers execute in the order they were registered."""
        order: list[int] = []

        def handler_1(event: DomainEvent) -> None:
            order.append(1)

        def handler_2(event: DomainEvent) -> None:
            order.append(2)

        def handler_3(event: DomainEvent) -> None:
            order.append(3)

        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.bus.register("test.event", handler_1)
        self.bus.register("test.event", handler_2)
        self.bus.register("test.event", handler_3)
        self.bus.dispatch(event)

        assert order == [1, 2, 3]

    def test_dispatch_for_unregistered_type_does_nothing(self) -> None:
        """Dispatching an event with no registered handlers is a no-op."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="unregistered",
        )
        # Should not raise
        self.bus.dispatch(event)
