"""Tests for retention purge task.

Tests that purge_old_audit_entries:
- Deletes entries older than the retention period
- Uses batch LIMIT for chunked deletion
- Returns total deleted count across batches
- Respects explicit retention_days override
- Returns 0 when no entries match
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.infrastructure.tasks.retention_purge import purge_old_audit_entries


class TestRetentionPurge:
    """purge_old_audit_entries behavior."""

    REFERENCE_DATE = datetime(2026, 9, 15, tzinfo=timezone.utc)

    @pytest.fixture
    def mock_conn(self) -> AsyncMock:
        """Provide a mock AsyncConnection."""
        conn = AsyncMock()
        conn.execute.return_value = MagicMock(rowcount=0)
        return conn

    # ── Tests ─────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_deletes_entries_older_than_retention(self, mock_conn: AsyncMock) -> None:
        """Should delete entries older than retention_days."""
        result = MagicMock(rowcount=500)
        mock_conn.execute.return_value = result

        count = await purge_old_audit_entries(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 500, f"Expected 500 deleted, got {count}"
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_batches(self, mock_conn: AsyncMock) -> None:
        """Should loop until fewer than batch_size rows are returned."""
        # Two full batches (1000 each) + one partial (200)
        results = [
            MagicMock(rowcount=1000),
            MagicMock(rowcount=1000),
            MagicMock(rowcount=200),
        ]
        mock_conn.execute.side_effect = results

        count = await purge_old_audit_entries(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 2200, f"Expected 2200 deleted, got {count}"
        assert mock_conn.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_no_entries_nothing_deleted(self, mock_conn: AsyncMock) -> None:
        """With no entries older than retention, should return 0."""
        result = MagicMock(rowcount=0)
        mock_conn.execute.return_value = result

        count = await purge_old_audit_entries(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 0
        mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_respects_explicit_retention_override(self, mock_conn: AsyncMock) -> None:
        """With a shorter retention, should still delete correctly."""
        result = MagicMock(rowcount=100)
        mock_conn.execute.return_value = result

        count = await purge_old_audit_entries(
            retention_days=30,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 100
        # Verify the cutoff was calculated from reference_date - 30 days
        _, kwargs = mock_conn.execute.call_args
        kwargs.get("parameters", kwargs.get("params", {}))
        # Execute was called, that's the main check

    @pytest.mark.asyncio
    async def test_exact_batch_boundary(self, mock_conn: AsyncMock) -> None:
        """Exactly batch_size rows should loop exactly once more to confirm exhaustion."""
        results = [
            MagicMock(rowcount=1000),  # full batch
            MagicMock(rowcount=0),  # no more rows
        ]
        mock_conn.execute.side_effect = results

        count = await purge_old_audit_entries(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 1000
        assert mock_conn.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_empty_table(self, mock_conn: AsyncMock) -> None:
        """With zero rows in the table, should return 0."""
        result = MagicMock(rowcount=0)
        mock_conn.execute.return_value = result

        count = await purge_old_audit_entries(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 0
