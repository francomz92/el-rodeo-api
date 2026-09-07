from abc import abstractmethod
from uuid import UUID

from src.cattle.domain.entities.schedule_events_entity import (
    ScheduleEventEntity,
    ScheduleEventRemindedEntity,
)
from src.cattle.domain.value_objects.schedule_event_value_object import (
    ScheduleEventCreationValueObject,
    ScheduleEventsListQueryParamsValueObject,
    ScheduleEventUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IScheduleEventRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> ScheduleEventEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, filters: ScheduleEventsListQueryParamsValueObject, order_by: str) -> list[ScheduleEventEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_events(self, tenant_id: UUID | None = None) -> list[ScheduleEventRemindedEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: ScheduleEventCreationValueObject) -> ScheduleEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def add_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: ScheduleEventUpdateValueObject) -> ScheduleEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def mark_as_notified(self, event_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
