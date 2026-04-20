from uuid import UUID

from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventUpdateDTO
from src.cattle.application.ports.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.exceptions import ConflictError, ResourceNotFoundError
from src.common.application.ports.uow import IUoW


class UpdateScheduleEventCase:

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow


    async def excecute(self, id: UUID, data: ScheduleEventUpdateDTO):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            event = await repository.get_by_id(id=id, user_id=data.user_id)
            if not event:
                raise ResourceNotFoundError("El evento que desea editar no existe")
            if not event.can_update():
                raise ConflictError("Este evento ya sucedió por lo que no se puede editar")
            return await repository.update_data(id=id, data=data)
            