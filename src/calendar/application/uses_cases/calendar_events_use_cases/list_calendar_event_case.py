from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.services.calendar_events.list_calendar_event_service import ListCalendarEventService
from src.calendar.domain.value_objects.calendar_event_value_object import CalendarEventsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW

# TODO: implement cursor-based pagination for consistency with list_animals_case


class ListCalendarEventsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListCalendarEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, filters: CalendarEventsListQueryParamsValueObject, order_by: str):
        async with self.uow as uow:
            repository = uow.get_repository(ICalendarEventRepository)
            return await self.service.get_events(query=filters, order_by=order_by, repository=repository)
