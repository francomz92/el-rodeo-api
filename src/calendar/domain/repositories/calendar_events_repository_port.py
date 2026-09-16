from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository

from ..entities.calendar_event_entity import (
    CalendarEventEntity,
    CalendarEventRemindedEntity,
)
from ..value_objects.calendar_event_value_object import (
    CalendarEventCreationValueObject,
    CalendarEventsListQueryParamsValueObject,
    CalendarEventUpdateValueObject,
)


class ICalendarEventRepository(IRepository):
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> CalendarEventEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_for_user(self, filters: CalendarEventsListQueryParamsValueObject, order_by: str) -> list[CalendarEventEntity]:
        raise NotImplementedError

    @abstractmethod
    async def get_pending_events(self, tenant_id: UUID | None = None) -> list[CalendarEventRemindedEntity]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: CalendarEventCreationValueObject) -> CalendarEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def add_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: CalendarEventUpdateValueObject) -> CalendarEventEntity:
        raise NotImplementedError

    @abstractmethod
    async def mark_as_notified(self, event_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
