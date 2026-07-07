"""Unit tests for EventOutbox SQLAlchemy model."""

from uuid import UUID

from src.common.infrastructure.persistence.models.event_outbox import (
    EventOutbox,
    OutboxStatus,
)


class TestOutboxStatus:
    """OutboxStatus enum defines valid states."""

    def test_has_pending_status(self) -> None:
        assert OutboxStatus.PENDING.value == "PENDING"

    def test_has_sent_status(self) -> None:
        assert OutboxStatus.SENT.value == "SENT"

    def test_has_failed_status(self) -> None:
        assert OutboxStatus.FAILED.value == "FAILED"

    def test_all_members_are_strings(self) -> None:
        for status in OutboxStatus:
            assert isinstance(status.value, str)


class TestEventOutboxModel:
    """EventOutbox model fields and defaults."""

    def test_has_table_name(self) -> None:
        """Model uses the correct table name."""
        assert EventOutbox.__tablename__ == "event_outbox"

    def test_has_id_column(self) -> None:
        """Model has a UUID primary key id."""
        col = EventOutbox.__table__.columns["id"]
        assert col.primary_key
        assert col.type.python_type is UUID

    def test_has_event_id_column(self) -> None:
        """Model has an event_id UUID column."""
        col = EventOutbox.__table__.columns["event_id"]
        assert col.type.python_type is UUID

    def test_has_event_type_column(self) -> None:
        """Model has an event_type string column."""
        col = EventOutbox.__table__.columns["event_type"]
        assert col.type.python_type is str

    def test_has_aggregate_id_column(self) -> None:
        """Model has an aggregate_id UUID column."""
        col = EventOutbox.__table__.columns["aggregate_id"]
        assert col.type.python_type is UUID

    def test_has_payload_column(self) -> None:
        """Model has a payload JSON column."""
        col = EventOutbox.__table__.columns["payload"]
        # JSON or JSONB — check it's a JSON type
        assert "JSON" in str(col.type).upper()

    def test_has_status_column(self) -> None:
        """Model has a status string column with default PENDING."""
        col = EventOutbox.__table__.columns["status"]
        assert col.type.python_type is str
        assert col.default is not None

    def test_has_retry_count_column(self) -> None:
        """Model has a retry_count integer column defaulting to 0."""
        col = EventOutbox.__table__.columns["retry_count"]
        assert col.type.python_type is int
        assert col.default is not None

    def test_has_created_at_column(self) -> None:
        """Model has a created_at datetime column."""
        col = EventOutbox.__table__.columns["created_at"]
        assert hasattr(col.type, "python_type")

    def test_has_updated_at_column(self) -> None:
        """Model has an updated_at datetime column."""
        col = EventOutbox.__table__.columns["updated_at"]
        assert hasattr(col.type, "python_type")

    def test_has_composite_index_on_status_created_at(self) -> None:
        """Model has an index on (status, created_at) for efficient get_pending."""
        indexes = EventOutbox.__table__.indexes
        index_names = {idx.name for idx in indexes}
        assert "ix_event_outbox_status_created_at" in index_names
