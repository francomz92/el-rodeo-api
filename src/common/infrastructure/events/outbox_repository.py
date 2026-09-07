"""Repository for transactional outbox table operations.

Provides CRUD-style methods on the ``event_outbox`` table used by the
outbox forwarder to fetch pending events and update their status.
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.infrastructure.persistence.models.event_outbox import (
    EventOutbox,
    OutboxStatus,
)

_MAX_RETRIES = 5


class OutboxRepository:
    """Repository for transactional outbox table operations.

    Wraps an ``AsyncSession`` and provides focused queries and mutations
    on the ``event_outbox`` table.  Does NOT manage transactions — callers
    are responsible for commit/rollback.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def add(self, event_outbox: EventOutbox) -> None:
        """Queue *event_outbox* for insertion during the next commit."""
        self.db.add(event_outbox)

    async def get_pending(self, limit: int = 100) -> list[EventOutbox]:
        """Return up to *limit* events ready for delivery.

        Includes PENDING events and FAILED events that still have retries
        remaining.  Events are returned oldest-first.
        """
        stmt = (
            select(EventOutbox)
            .where(
                or_(
                    EventOutbox.status == OutboxStatus.PENDING,
                    (EventOutbox.status == OutboxStatus.FAILED) & (EventOutbox.retry_count < _MAX_RETRIES),
                )
            )
            .order_by(EventOutbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def mark_sent(self, event_outbox: EventOutbox) -> None:
        """Mark *event_outbox* as successfully forwarded."""
        event_outbox.status = OutboxStatus.SENT

    async def mark_failed(self, event_outbox: EventOutbox) -> None:
        """Mark *event_outbox* as permanently failed."""
        event_outbox.status = OutboxStatus.FAILED
