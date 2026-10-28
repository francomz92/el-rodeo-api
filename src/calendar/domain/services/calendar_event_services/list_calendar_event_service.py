from ...entities.calendar_event_entity import CalendarEventEntity
from ...repositories.calendar_events_repository_port import ICalendarEventRepository
from ...value_objects.calendar_event_value_object import CalendarEventsListQueryParamsValueObject


class ListCalendarEventService:
    async def get_events(
        self,
        query: CalendarEventsListQueryParamsValueObject,
        order_by: str,
        repository: ICalendarEventRepository,
    ) -> list[CalendarEventEntity]:
        events_list = await repository.list_for_user(
            filters=query,
            order_by=order_by,
        )
        return events_list
