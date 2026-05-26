from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.update_schedule_event_service import UpdateScheduleEventService
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventUpdateValueObject
from src.common.application.ports.uow import IUoW


class UpdateScheduleEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateScheduleEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, data: ScheduleEventUpdateValueObject):
        async with self.uow as uow:
            self.service.validate_event_date(data.event_date)
            repository = uow.get_repository(IScheduleEventRepository)
            await self.service.validate_event_exists(
                id=id,
                user_id=data.user_id,
                repository=repository,
            )
            await self.service.update_event_data(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()
