from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.list_schedule_event_service import ListScheduleEventService
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW


class ListScheduleEventsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListScheduleEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            return await self.service.get_events(
                user_id=user_id,
                query=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
