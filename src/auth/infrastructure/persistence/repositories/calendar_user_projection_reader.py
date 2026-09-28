from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.infrastructure.persistence.models import User
from src.calendar.domain.entities.calendar_user_projection import CalendarUserProjection
from src.calendar.domain.repositories.calendar_user_projection_port import ICalendarUserProjectionReader


class CalendarUserProjectionReader(ICalendarUserProjectionReader):
    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_users_by_ids(self, user_ids: set[UUID]) -> dict[UUID, CalendarUserProjection]:
        if not user_ids:
            return {}

        stmt = select(User.id, User.name, User.email).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        rows = result.mappings().all()
        return {
            row["id"]: CalendarUserProjection(
                id=row["id"],
                name=row["name"],
                email=row["email"],
            )
            for row in rows
        }
