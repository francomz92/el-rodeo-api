from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.list_schedule_event_service import ListScheduleEventService
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW

# TODO: implement cursor-based pagination for consistency with list_animals_case


class ListScheduleEventsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListScheduleEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, filters: ScheduleEventsListQueryParamsValueObject, order_by: str):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            return await self.service.get_events(query=filters, order_by=order_by, repository=repository)
