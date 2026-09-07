"""Retention purge: batch DELETE old audit_log entries.

Usage:
    python -m src.common.infrastructure.tasks.retention_purge --days 180

Deletes entries older than *retention_days* in batches of 1000 to avoid
long-running locks on the audit_log table.
"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from src.common.infrastructure.core._config import settings

_BATCH_SIZE = 1000


async def purge_old_audit_entries(
    retention_days: int = 180,
    connection: AsyncConnection | None = None,
    reference_date: datetime | None = None,
) -> int:
    """Delete audit_log entries older than the retention period.

    Deletes in batches of {_BATCH_SIZE} to avoid long-running locks.
    Each batch is self-contained — safe to interrupt and resume.

    Args:
        retention_days: Age in days beyond which an entry is eligible for DELETE.
        connection: An async DB connection. If None, creates its own (for CLI use).
        reference_date: Override "now" for deterministic testing. Defaults to UTC now.

    Returns:
        Number of rows deleted.
    """
    now = reference_date or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=retention_days)
    total_deleted = 0

    stmt = text("DELETE FROM audit_log WHERE id IN (SELECT id FROM audit_log WHERE created_at < :cutoff LIMIT :batch_size)")

    async def _purge(conn: AsyncConnection) -> None:
        nonlocal total_deleted

        while True:
            result = await conn.execute(
                stmt,
                {"cutoff": cutoff, "batch_size": _BATCH_SIZE},
            )
            total_deleted += result.rowcount
            if result.rowcount < _BATCH_SIZE:
                break

    if connection is not None:
        await _purge(connection)
    else:
        engine = create_async_engine(settings.DB_URL)
        async with engine.begin() as conn:
            await _purge(conn)
        await engine.dispose()

    return total_deleted


# ── CLI entry point ────────────────────────────────────────────────────────────


def main() -> None:
    """CLI entry point for manual retention purge."""
    parser = argparse.ArgumentParser(
        description="Delete old audit_log entries from the database.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Retention period in days (default: 180)",
    )
    args = parser.parse_args()

    count = asyncio.run(purge_old_audit_entries(retention_days=args.days))
    print(f"Deleted {count} old audit_log entrie(s).")


if __name__ == "__main__":
    main()
