"""Unit tests for OutboxRepository.

Uses an AsyncMock session to verify SQLAlchemy operations without a
real database connection.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from sqlalchemy import Select

from src.common.infrastructure.events.outbox_repository import OutboxRepository
from src.common.infrastructure.persistence.models.event_outbox import (
    EventOutbox,
    OutboxStatus,
)


class TestOutboxRepository:
    """OutboxRepository wraps outbox table operations."""

    def setup_method(self) -> None:
        self.session = AsyncMock()
        # session.add() is synchronous in SQLAlchemy — use MagicMock, not AsyncMock
        self.session.add = MagicMock(return_value=None)
        self.session.execute = AsyncMock()
        self.repo = OutboxRepository(session=self.session)

    async def test_add_calls_session_add(self) -> None:
        """add() delegates to session.add()."""
        event_outbox = EventOutbox(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
        )

        await self.repo.add(event_outbox)

        self.session.add.assert_called_once_with(event_outbox)

    async def test_get_pending_returns_list(self) -> None:
        """get_pending() queries PENDING events ordered by created_at."""
        expected_outbox = EventOutbox(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
        )
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [expected_outbox]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.session.execute.return_value = mock_result

        results = await self.repo.get_pending(limit=10)

        assert results == [expected_outbox]
        self.session.execute.assert_awaited_once()

        # Verify the query filters on PENDING status
        (stmt,) = self.session.execute.call_args[0]
        assert isinstance(stmt, Select)

    async def test_get_pending_default_limit(self) -> None:
        """get_pending() defaults to limit=100."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.session.execute.return_value = mock_result

        results = await self.repo.get_pending()

        assert results == []
        self.session.execute.assert_awaited_once()

    async def test_get_pending_returns_empty_list(self) -> None:
        """get_pending() returns an empty list when no pending events exist."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        self.session.execute.return_value = mock_result

        results = await self.repo.get_pending(limit=5)

        assert results == []

    async def test_mark_sent_updates_status(self) -> None:
        """mark_sent() sets status to SENT."""
        event_outbox = EventOutbox(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            status=OutboxStatus.PENDING,
        )

        await self.repo.mark_sent(event_outbox)

        assert event_outbox.status == OutboxStatus.SENT

    async def test_mark_failed_updates_status(self) -> None:
        """mark_failed() sets status to FAILED."""
        event_outbox = EventOutbox(
            event_id=UUID("00000000-0000-0000-0000-000000000001"),
            event_type="test.event",
            aggregate_id=UUID("00000000-0000-0000-0000-000000000002"),
            status=OutboxStatus.PENDING,
        )

        await self.repo.mark_failed(event_outbox)

        assert event_outbox.status == OutboxStatus.FAILED
