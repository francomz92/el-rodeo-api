from uuid import UUID

from src.calendar.domain.events.calendar_events import CalendarEventUpdated
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.services.calendar_events.update_calendar_event_service import UpdateCalendarEventService
from src.calendar.domain.value_objects.calendar_event_value_object import CalendarEventUpdateValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class UpdateCalendarEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateCalendarEventService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, id: UUID, data: CalendarEventUpdateValueObject):
        async with self.uow as uow:
            self.service.validate_event_date(data)
            repository = uow.get_repository(ICalendarEventRepository)
            await self.service.validate_event_exists(
                id=id,
                repository=repository,
            )
            schedule_event = await self.service.update_event_data(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()

        await self.event_bus.dispatch(CalendarEventUpdated(aggregate_id=id))
        return schedule_event
