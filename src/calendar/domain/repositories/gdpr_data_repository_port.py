"""Repository port for Calendar-owned GDPR unlink and export reads."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class ICalendarGDPRDataRepository(IRepository):
    """Calendar-owned GDPR data access.

    Implementations operate inside the caller's Unit of Work transaction
    boundary and never commit.
    """

    @abstractmethod
    async def unlink_user_data(self, user_id: UUID) -> None:
        """Detach the user from Calendar-owned business rows.

        Sets ``CalendarEvent.user_id`` to NULL for matching rows and deletes
        the user's ``CalendarEventParticipant`` rows (its ``user_id`` is a
        non-null composite primary key column and cannot be nulled).
        """
        raise NotImplementedError

    @abstractmethod
    async def fetch_schedule_events(self, user_id: UUID) -> list[dict]:
        """Return all-column mappings of ``CalendarEvent`` rows for the user.

        Participant links are never exported.
        """
        raise NotImplementedError
