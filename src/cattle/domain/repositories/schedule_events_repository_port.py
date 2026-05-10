from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.cattle.domain.value_objects.schedule_event_value_object import (
    ScheduleEventCreationValueObject,
    ScheduleEventsListQueryParamsValueObject,
    ScheduleEventUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IScheduleEventRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> ScheduleEventEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[ScheduleEventEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_events(self, user_id: UUID) -> list[ScheduleEventEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: ScheduleEventCreationValueObject) -> ScheduleEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: ScheduleEventUpdateValueObject) -> ScheduleEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
