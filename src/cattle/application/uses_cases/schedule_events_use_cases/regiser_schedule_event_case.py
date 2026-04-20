from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventCreationDTO
from src.cattle.application.ports.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.ports.uow import IUoW


class RegisterScheduleEventCase:

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def excecue(self, data: ScheduleEventCreationDTO):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            return await repository.create(data=data)
