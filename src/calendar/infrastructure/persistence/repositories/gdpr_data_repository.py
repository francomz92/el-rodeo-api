"""SQLAlchemy implementation of ICalendarGDPRDataRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.calendar.domain.repositories.gdpr_data_repository_port import (
    ICalendarGDPRDataRepository,
)
from src.calendar.infrastructure.persistence.models import (
    CalendarEvent,
    CalendarEventParticipant,
)


class CalendarGDPRDataRepository(ICalendarGDPRDataRepository):
    """Calendar-owned GDPR unlink and export queries.

    User-scoped and tenant-agnostic: current GDPR queries filter only by
    ``user_id``. Executes inside the caller's Unit of Work transaction and
    never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def unlink_user_data(self, user_id: UUID) -> None:
        await self.db.execute(update(CalendarEvent).where(CalendarEvent.user_id == user_id).values(user_id=None))
        await self.db.execute(delete(CalendarEventParticipant).where(CalendarEventParticipant.user_id == user_id))

    async def fetch_schedule_events(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(CalendarEvent.__table__).where(CalendarEvent.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]
