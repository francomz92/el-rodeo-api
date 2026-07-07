"""Retention purge: DROP old audit_log partitions.

Usage:
    python -m src.common.infrastructure.tasks.retention_purge --days 180

Uses the audit_log_YYYY_MM partition naming convention. Only partitions
matching this exact pattern are eligible for DROP — non-standard partition
names (e.g., audit_log_past) are preserved as a safety measure.
"""

import argparse
import asyncio
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from src.common.infrastructure.core._config import settings

# ── Constants ─────────────────────────────────────────────────────────────────

_AUDIT_LOG_PARTITION_PATTERN = re.compile(r"^audit_log_(\d{4})_(\d{2})$")

# Months with 31 days (everything else is 30 for the last-day calculation)
_MONTHS_WITH_31_DAYS = {1, 3, 5, 7, 8, 10, 12}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _last_day_of_month(year: int, month: int) -> int:
    """Return the last day of the given month.

    Handles leap years for February.
    """
    if month == 2:
        # Leap year check
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        return 28
    if month in _MONTHS_WITH_31_DAYS:
        return 31
    return 30


def _parse_partition_name(name: str) -> tuple[int, int] | None:
    """Parse an audit_log partition name into (year, month).

    Returns None if the name does not match the expected pattern.
    This is a safety guard against SQL injection and accidental DROPs.
    """
    match = _AUDIT_LOG_PARTITION_PATTERN.match(name)
    if not match:
        return None
    year = int(match.group(1))
    month = int(match.group(2))
    if month < 1 or month > 12:
        return None
    return (year, month)


async def get_audit_log_partitions(
    connection: AsyncConnection,
) -> list[str]:
    """Query the database for all partition tables of the audit_log table.

    Returns a list of partition names (without schema qualifier).
    """
    result = await connection.execute(
        text("""
            SELECT inhrelid::regclass::text AS partition_name
            FROM pg_inherits
            WHERE inhparent = 'audit_log'::regclass
        """)
    )
    rows = result.fetchall()
    partitions: list[str] = []
    for row in rows:
        name: str = row[0]
        # Strip schema qualifier if present (e.g. "public.audit_log_2026_06")
        if "." in name:
            name = name.split(".", 1)[1]
        partitions.append(name)
    return partitions


async def purge_old_audit_partitions(
    retention_days: int = 180,
    connection: AsyncConnection | None = None,
    reference_date: datetime | None = None,
) -> int:
    """Drop audit_log partitions older than the retention period.

    Args:
        retention_days: Age in days beyond which a partition is eligible for DROP.
        connection: An async DB connection. If None, creates its own (for CLI use).
        reference_date: Override "now" for deterministic testing. Defaults to UTC now.

    Returns:
        Number of partitions dropped.

    Safety:
        - Only drops tables matching the ``audit_log_YYYY_MM`` naming convention.
        - Uses parameterized SQL via SQLAlchemy text() for the query.
        - The DROP TABLE statement is constructed with a validated table name.
    """
    now = reference_date or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    dropped_count = 0

    async def _purge(conn: AsyncConnection) -> None:
        nonlocal dropped_count

        partitions = await get_audit_log_partitions(conn)

        for name in partitions:
            parsed = _parse_partition_name(name)
            if parsed is None:
                # Skip non-standard partition names (safety guard)
                continue

            year, month = parsed
            last_day = _last_day_of_month(year, month)
            # The partition covers data up to the start of the NEXT month,
            # so the last full date in this partition is the last day of the current month.
            partition_end = datetime(
                year,
                month,
                last_day,
                tzinfo=timezone.utc,
            )

            if partition_end < cutoff:
                # Drop the partition
                await conn.execute(text(f"DROP TABLE IF EXISTS {name} CASCADE"))
                dropped_count += 1

    if connection is not None:
        await _purge(connection)
    else:
        engine = create_async_engine(settings.DB_URL)
        async with engine.connect() as conn:
            await _purge(conn)
        await engine.dispose()

    return dropped_count


# ── CLI entry point ────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for manual partition purge."""
    parser = argparse.ArgumentParser(
        description="Drop old audit_log partitions from the database.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Retention period in days (default: 180)",
    )
    args = parser.parse_args()

    count = asyncio.run(purge_old_audit_partitions(retention_days=args.days))
    print(f"Dropped {count} old audit_log partition(s).")


if __name__ == "__main__":
    main()
