from src.cattle.domain.events.animal_events import ScheduleEventCreated
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.register_schedule_event_service import RegisterScheduleEventService
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventCreationValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus


class RegisterScheduleEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: RegisterScheduleEventService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, data: ScheduleEventCreationValueObject):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            event = await self.service.create_new(
                data=data,
                repository=repository,
            )
            await uow.commit()

        await self.event_bus.dispatch(ScheduleEventCreated(aggregate_id=event.id))
        return event
