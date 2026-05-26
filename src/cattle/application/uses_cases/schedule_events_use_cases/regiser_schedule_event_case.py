from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.register_schedule_event_service import RegisterScheduleEventService
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventCreationValueObject
from src.common.application.ports.uow import IUoW


class RegisterScheduleEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: RegisterScheduleEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def excecue(self, data: ScheduleEventCreationValueObject):
        async with self.uow as uow:
            self.service.validate_event_date(data.event_date)
            repository = uow.get_repository(IScheduleEventRepository)
            await self.service.create_new(
                data=data,
                repository=repository,
            )
            await uow.commit()
