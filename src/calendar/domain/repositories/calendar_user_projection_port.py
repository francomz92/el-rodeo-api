from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository

from ..entities.calendar_user_projection import CalendarUserProjection


class ICalendarUserProjectionReader(IRepository):
    @abstractmethod
    async def get_users_by_ids(self, user_ids: set[UUID]) -> dict[UUID, CalendarUserProjection]:
        raise NotImplementedError
