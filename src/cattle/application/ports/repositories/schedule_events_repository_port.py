from abc import abstractmethod
from uuid import UUID

from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventCreationDTO, ScheduleEventUpdateDTO, ScheduleEventsListQueryParamsDTO
from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.common.application.ports.repository import IRepository


class IScheduleEventRepository(IRepository):
    @abstractmethod
    async def get_by_id(self, id: UUID, user_id: UUID) -> ScheduleEventEntity | None:
        raise NotImplemented
    
    @abstractmethod
    async def list_for_user(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsDTO,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[ScheduleEventEntity]:
        raise NotImplemented

    @abstractmethod
    async def get_pending_events(self, user_id: UUID) -> list[ScheduleEventEntity]:
        raise NotImplemented

    @abstractmethod
    async def create(self, data: ScheduleEventCreationDTO) -> ScheduleEventEntity:
        raise NotImplemented

    @abstractmethod
    async def update_data(self, id: UUID, data: ScheduleEventUpdateDTO) -> ScheduleEventEntity:
        raise NotImplemented

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplemented
