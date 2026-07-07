"""Unit tests for DomainEvent base dataclass and typed events."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.billing.domain.events.payment_events import PaymentReceived
from src.cattle.domain.events.animal_events import AnimalCreated
from src.common.domain.events.base import DomainEvent


class TestDomainEvent:
    """DomainEvent base dataclass creates events with proper defaults."""

    def test_creates_event_with_required_fields(self) -> None:
        """Given aggregate_id and event_type, creates a DomainEvent with
        auto-generated UUID and UTC timestamp."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        assert isinstance(event.event_id, UUID)
        assert event.event_id is not None
        assert event.aggregate_id == UUID("00000000-0000-0000-0000-000000000001")
        assert event.event_type == "test.event"
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp is not None

    def test_event_id_is_unique_per_instance(self) -> None:
        """Each event gets a distinct UUID."""
        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="test.event",
        )

        assert event_a.event_id != event_b.event_id

    def test_timestamp_is_utc(self) -> None:
        """Event timestamp is timezone-aware and in UTC."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo.utcoffset(None) == timezone.utc.utcoffset(None)

    def test_metadata_defaults_to_empty_dict(self) -> None:
        """Without metadata, event.metadata is an empty dict."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        assert event.metadata == {}

    def test_metadata_can_be_passed_explicitly(self) -> None:
        """Given custom metadata, event.metadata contains the provided entries."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            metadata={"trace_id": "abc-123", "source": "api"},
        )

        assert event.metadata["trace_id"] == "abc-123"
        assert event.metadata["source"] == "api"
        assert len(event.metadata) == 2

    def test_event_is_immutable(self) -> None:
        """DomainEvent is frozen — cannot modify attributes after creation."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )

        with pytest.raises(AttributeError):
            event.event_type = "changed"

    def test_aggregate_id_is_uuid(self) -> None:
        """aggregate_id parameter accepts and stores a UUID."""
        aggregate_id = UUID("00000000-0000-0000-0000-000000000001")
        event = DomainEvent(
            aggregate_id=aggregate_id,
            event_type="test.event",
        )

        assert event.aggregate_id == aggregate_id


class TestAnimalCreated:
    """AnimalCreated typed event carries animal.created event_type."""

    def test_creates_with_default_event_type(self) -> None:
        """AnimalCreated has event_type='animal.created' by default."""
        animal_id = UUID("00000000-0000-0000-0000-000000000001")
        event = AnimalCreated(aggregate_id=animal_id)

        assert event.event_type == "animal.created"
        assert event.aggregate_id == animal_id
        assert isinstance(event.event_id, UUID)

    def test_instantiation_with_different_animal_id(self) -> None:
        """AnimalCreated accepts any UUID as aggregate_id."""
        animal_id = UUID("11111111-1111-1111-1111-111111111111")
        event = AnimalCreated(aggregate_id=animal_id)

        assert event.aggregate_id == animal_id


class TestPaymentReceived:
    """PaymentReceived typed event carries payment.received event_type."""

    def test_creates_with_default_event_type(self) -> None:
        """PaymentReceived has event_type='payment.received' by default."""
        payment_id = UUID("00000000-0000-0000-0000-000000000001")
        event = PaymentReceived(aggregate_id=payment_id)

        assert event.event_type == "payment.received"
        assert event.aggregate_id == payment_id
        assert isinstance(event.event_id, UUID)

    def test_instantiation_with_different_payment_id(self) -> None:
        """PaymentReceived accepts any UUID as aggregate_id."""
        payment_id = UUID("22222222-2222-2222-2222-222222222222")
        event = PaymentReceived(aggregate_id=payment_id)

        assert event.aggregate_id == payment_id
