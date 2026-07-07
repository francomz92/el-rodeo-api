"""Unit tests for UnitOfWork outbox flush and rollback behavior.

NOTE: ``session.add()`` is synchronous in SQLAlchemy (not an async method).
We use a sync ``MagicMock`` for ``.add`` because ``AsyncMock`` attribute
access returns an ``AsyncMock`` whose call produces a coroutine — and with
``asyncio_default_fixture_loop_scope = "session"`` those unawaited
coroutines accumulate across tests and corrupt the shared event loop.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from src.common.domain.events.base import DomainEvent
from src.common.infrastructure.persistence.models.event_outbox import EventOutbox
from src.common.infrastructure.persistence.uow import UnitOfWork


class TestUnitOfWorkOutboxFlush:
    """UnitOfWork inserts outbox events during commit()."""

    def setup_method(self) -> None:
        self.session = AsyncMock()
        # session.add() is synchronous — must NOT be an AsyncMock
        self.session.add = MagicMock(return_value=None)
        self.session.connection = AsyncMock()
        self.uow = UnitOfWork(session=self.session)

    def test_flush_outbox_creates_event_model(self) -> None:
        """_flush_outbox_events() creates EventOutbox with correct fields."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            metadata={"key": "value"},
        )
        self.uow.add_outbox_event(event)

        self.uow._flush_outbox_events()

        self.session.add.assert_called_once()
        (added,) = self.session.add.call_args[0]
        assert isinstance(added, EventOutbox)
        assert added.event_id == event.event_id
        assert added.event_type == "test.event"
        assert added.aggregate_id == event.aggregate_id
        assert added.payload["event_id"] == str(event.event_id)
        assert added.payload["event_type"] == "test.event"
        assert added.payload["metadata"] == {"key": "value"}

    def test_flush_outbox_clears_events(self) -> None:
        """After flushing, outbox_events list is cleared."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.uow.add_outbox_event(event)
        self.uow._flush_outbox_events()

        assert len(self.uow.outbox_events) == 0

    def test_flush_outbox_handles_multiple_events(self) -> None:
        """Multiple queued events are all flushed."""
        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.a",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="test.b",
        )
        self.uow.add_outbox_event(event_a)
        self.uow.add_outbox_event(event_b)

        self.uow._flush_outbox_events()

        assert self.session.add.call_count == 2
        added_types = {type(call[0][0]) for call in self.session.add.call_args_list}
        assert EventOutbox in added_types

    def test_flush_outbox_is_noop_when_empty(self) -> None:
        """Flushing with no queued events does nothing."""
        self.uow._flush_outbox_events()

        self.session.add.assert_not_called()

    async def test_commit_flushes_outbox_before_db_commit(self) -> None:
        """commit() calls _flush_outbox_events, then *flush*, then db.commit()."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.uow.add_outbox_event(event)

        with patch.object(self.uow, "_do_audit_flush", AsyncMock()) as mock_audit:
            await self.uow.commit()

            # Hooks ran, audit was flushed
            mock_audit.assert_called_once()
            # Outbox event was flushed (added to session)
            self.session.add.assert_called_once()
            (added,) = self.session.add.call_args[0]
            assert isinstance(added, EventOutbox)
            # db.commit() was called after the outbox flush
            self.session.commit.assert_awaited_once()

    async def test_commit_handles_multiple_outbox_events(self) -> None:
        """commit() flushes all queued outbox events."""
        event_a = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.a",
        )
        event_b = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            event_type="test.b",
        )
        self.uow.add_outbox_event(event_a)
        self.uow.add_outbox_event(event_b)

        with patch.object(self.uow, "_do_audit_flush", AsyncMock()):
            await self.uow.commit()

            assert self.session.add.call_count == 2
            self.session.commit.assert_awaited_once()

    async def test_commit_without_outbox_events_still_works(self) -> None:
        """commit() works normally when no outbox events are queued."""
        with patch.object(self.uow, "_do_audit_flush", AsyncMock()):
            await self.uow.commit()

            self.session.add.assert_not_called()
            self.session.commit.assert_awaited_once()


class TestUnitOfWorkOutboxRollback:
    """UoW rollback clears outbox_events."""

    def setup_method(self) -> None:
        self.session = AsyncMock()
        self.session.connection = AsyncMock()
        self.uow = UnitOfWork(session=self.session)

    async def test_rollback_clears_outbox_events(self) -> None:
        """After rollback, outbox_events is empty."""
        event = DomainEvent(
            aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
        )
        self.uow.add_outbox_event(event)
        assert len(self.uow.outbox_events) == 1

        await self.uow.rollback()

        assert len(self.uow.outbox_events) == 0

    async def test_rollback_with_no_outbox_events_does_not_error(self) -> None:
        """Rollback when no events queued does not error."""
        await self.uow.rollback()

        assert len(self.uow.outbox_events) == 0

    async def test_rollback_clears_audit_and_outbox(self) -> None:
        """Rollback clears both audit queue and outbox events."""
        with patch.object(self.uow.audit_repository, "clear") as mock_clear:
            event = DomainEvent(
                aggregate_id=UUID("00000000-0000-0000-0000-000000000001"),
                event_type="test.event",
            )
            self.uow.add_outbox_event(event)
            await self.uow.rollback()

            mock_clear.assert_called_once()
            assert len(self.uow.outbox_events) == 0
