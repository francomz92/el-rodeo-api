"""Tests for retention purge task (PR 4, Tasks 4.1–4.5).

Tests that purge_old_audit_partitions:
- Correctly identifies and drops old partitions
- Does NOT drop partitions within retention period
- Does NOT drop non-audit_log tables
- Respects explicit retention_days override
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.infrastructure.tasks.retention_purge import purge_old_audit_partitions


class TestRetentionPurge:
    """Task 4.4: purge_old_audit_partitions behavior."""

    REFERENCE_DATE = datetime(2026, 9, 15, tzinfo=timezone.utc)

    @pytest.fixture
    def mock_conn(self) -> AsyncMock:
        """Provide a mock AsyncConnection with execute returning empty by default."""
        conn = AsyncMock()
        # Default: execute returns a result with no rows
        default_result = MagicMock()
        default_result.fetchall.return_value = []
        conn.execute.return_value = default_result
        return conn

    @pytest.fixture
    def partition_rows(self) -> list[tuple[str]]:
        """Return a list of audit_log partition names in the database."""
        return [
            ("audit_log_2026_01",),  # Jan 2026 → cutoff = Sep15 - 180d = Mar19  → DROP
            ("audit_log_2026_02",),  # Feb 2026 → DROP
            ("audit_log_2026_03",),  # Mar 2026 → ends Mar31 > Mar19 → KEEP (partially in window)
            ("audit_log_2026_06",),  # Jun 2026 → ends Jun30 > Mar19 → KEEP
            ("audit_log_2026_09",),  # Sep 2026 → KEEP
        ]

    # ── Tests ─────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_drops_partitions_older_than_retention(self, mock_conn: AsyncMock, partition_rows: list[tuple[str]]) -> None:
        """Should drop only partitions whose month ends before the retention cut-off."""
        # Arrange: query returns partition rows
        query_result = MagicMock()
        query_result.fetchall.return_value = partition_rows
        mock_conn.execute.return_value = query_result

        # Act
        count = await purge_old_audit_partitions(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        # Assert: only Jan and Feb are older than March 19, 2026 (Sep15 - 180d)
        assert count == 2, f"Expected 2 drops, got {count}"

        # Verify DROP TABLE was called for each old partition
        # First call is the partition query, subsequent calls are DROPs
        assert mock_conn.execute.call_count == 3, f"Expected 3 execute calls (1 query + 2 DROPs), got {mock_conn.execute.call_count}"

        # Extract SQL text from TextClause objects
        drop_sqls = []
        for call_args in mock_conn.execute.call_args_list[1:]:  # skip first (query)
            sql_text = call_args[0][0].text
            drop_sqls.append(sql_text)

        drop_names = set()
        for sql in drop_sqls:
            # Extract table name from DROP TABLE IF EXISTS <name>
            parts = sql.split()
            for i, part in enumerate(parts):
                if part.upper() == "TABLE" and i + 3 < len(parts):
                    drop_names.add(parts[i + 3].rstrip(";"))

        assert "audit_log_2026_01" in drop_names, "Should drop Jan 2026 partition"
        assert "audit_log_2026_02" in drop_names, "Should drop Feb 2026 partition"

    @pytest.mark.asyncio
    async def test_keeps_partitions_within_retention(self, mock_conn: AsyncMock, partition_rows: list[tuple[str]]) -> None:
        """Should NOT drop partitions whose month ends within the retention period."""
        query_result = MagicMock()
        query_result.fetchall.return_value = partition_rows
        mock_conn.execute.return_value = query_result

        count = await purge_old_audit_partitions(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        # Verify the DROPs are only for old partitions
        drop_sqls_list = [
            call_args[0][0].text
            for call_args in mock_conn.execute.call_args_list[1:]  # skip query
        ]
        drop_sqls = " ".join(drop_sqls_list)

        # Partitions within retention should NOT be in any DROP
        assert "audit_log_2026_03" not in drop_sqls, "Mar 2026 should be kept"
        assert "audit_log_2026_06" not in drop_sqls, "Jun 2026 should be kept"
        assert "audit_log_2026_09" not in drop_sqls, "Sep 2026 should be kept"

    @pytest.mark.asyncio
    async def test_does_not_drop_non_audit_log_tables(self, mock_conn: AsyncMock) -> None:
        """Should NOT drop tables that don't match the audit_log_YYYY_MM pattern."""
        # Mix of valid audit_log partitions and other tables
        query_result = MagicMock()
        query_result.fetchall.return_value = [
            ("audit_log_2026_01",),  # valid → DROP
            ("audit_log_2026_past",),  # NOT a YYYY_MM pattern → KEEP
            ("audit_log_extra",),  # NOT a pattern → KEEP
            ("animals",),  # NOT audit_log at all → KEEP
            ("audit_log_wrong_format",),  # NOT a pattern → KEEP
        ]
        mock_conn.execute.return_value = query_result

        count = await purge_old_audit_partitions(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        # Only audit_log_2026_01 should be dropped
        assert count == 1, f"Expected 1 drop, got {count}"
        drop_sqls_list = [
            call_args[0][0].text
            for call_args in mock_conn.execute.call_args_list[1:]  # skip query
        ]
        drop_sqls = " ".join(drop_sqls_list)

        # Verify non-standard names are NOT in DROP statements
        assert "audit_log_2026_past" not in drop_sqls, "Should not drop non-standard pattern"
        assert "audit_log_extra" not in drop_sqls
        assert "animals" not in drop_sqls, "Should not drop non-audit_log tables"

    @pytest.mark.asyncio
    async def test_respects_explicit_retention_override(self, mock_conn: AsyncMock, partition_rows: list[tuple[str]]) -> None:
        """With a shorter retention, more partitions should be kept."""
        # Set up: same partitions, but 30-day retention instead of 180
        query_result = MagicMock()
        query_result.fetchall.return_value = partition_rows
        mock_conn.execute.return_value = query_result

        # 30 days from Sep 15 = Aug 16 cutoff
        # Only Jan 2026 (ends Jan 31) and Feb 2026 (ends Feb 28) are before Aug 16
        # Wait — no, with 30-day retention:
        #   cutoff = Sep15 - 30 = Aug 16
        #   Jan 31 < Aug 16 → DROP
        #   Feb 28 < Aug 16 → DROP
        #   Mar 31 < Aug 16 → DROP
        #   Jun 30 < Aug 16 → DROP
        #   Sep 30 > Aug 16 → KEEP
        # That's 4 drops.
        count = await purge_old_audit_partitions(
            retention_days=30,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 4, f"Expected 4 drops with 30-day retention, got {count}"

        # First call is query, remaining 4 are DROPs
        assert mock_conn.execute.call_count == 5, f"Expected 5 calls (1 query + 4 DROPs), got {mock_conn.execute.call_count}"

        # Sep 2026 should be kept (it's within 30 days)
        drop_sqls_list = [
            call_args[0][0].text
            for call_args in mock_conn.execute.call_args_list[1:]  # skip query
        ]
        drop_sqls = " ".join(drop_sqls_list)
        assert "audit_log_2026_09" not in drop_sqls

    @pytest.mark.asyncio
    async def test_no_old_partitions_nothing_dropped(self, mock_conn: AsyncMock) -> None:
        """With zero-day retention or all partitions new, nothing is dropped."""
        query_result = MagicMock()
        # All partitions are current
        current_month = self.REFERENCE_DATE.strftime("audit_log_%Y_%m")
        query_result.fetchall.return_value = [(current_month,)]
        mock_conn.execute.return_value = query_result

        count = await purge_old_audit_partitions(
            retention_days=1,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 0, "Should not drop the current month partition"

    @pytest.mark.asyncio
    async def test_empty_partition_list(self, mock_conn: AsyncMock) -> None:
        """With no partitions at all, should return 0."""
        query_result = MagicMock()
        query_result.fetchall.return_value = []
        mock_conn.execute.return_value = query_result

        count = await purge_old_audit_partitions(
            retention_days=180,
            connection=mock_conn,
            reference_date=self.REFERENCE_DATE,
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_sql_injection_safe(self, mock_conn: AsyncMock) -> None:
        """Should not DROP tables with malicious names that don't match the pattern."""
        query_result = MagicMock()
        query_result.fetchall.return_value = [
            ("audit_log_2026_01",),  # valid
            ("audit_log_2026_; DROP TABLE users;",),  # malicious injection
            ("audit_log_9999_99",),  # invalid month
        ]
        mock_conn.execute.return_value = query_result

        count = await purge_old_audit_partitions(
            retention_days=180,
            connection=mock_conn,
            reference_date=datetime(2027, 1, 15, tzinfo=timezone.utc),
        )

        # Only audit_log_2026_01 should be considered
        assert count == 1
