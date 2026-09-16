from src.calendar.domain.events.calendar_events import CalendarEventCreated
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.services.calendar_events.register_calendar_event_service import RegisterCalendarEventService
from src.calendar.domain.value_objects.calendar_event_value_object import CalendarEventCreationValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class RegisterCalendarEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: RegisterCalendarEventService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, data: CalendarEventCreationValueObject):
        async with self.uow as uow:
            repository = uow.get_repository(ICalendarEventRepository)
            event = await self.service.create_new(
                data=data,
                repository=repository,
            )
            await uow.commit()

        await self.event_bus.dispatch(CalendarEventCreated(aggregate_id=event.id))
        return event
