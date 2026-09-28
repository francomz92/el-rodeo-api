from src.calendar.domain.entities.calendar_event_entity import CalendarEventParticipantEntity
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.repositories.calendar_user_projection_port import ICalendarUserProjectionReader
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
            events = await self.service.get_events(query=filters, order_by=order_by, repository=repository)
            user_reader = uow.get_repository(ICalendarUserProjectionReader)
            user_ids = {user_id for event in events for user_id in event.participant_user_ids}
            users_by_id = await user_reader.get_users_by_ids(user_ids)
            for event in events:
                event.participants = [
                    CalendarEventParticipantEntity(id=user_id, name=users_by_id[user_id].name)
                    for user_id in event.participant_user_ids
                    if user_id in users_by_id
                ]
            return events
