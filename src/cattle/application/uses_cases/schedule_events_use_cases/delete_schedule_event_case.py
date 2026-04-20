from uuid import UUID

from src.cattle.application.ports.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.exceptions import ConflictError, ResourceNotFoundError
from src.common.application.ports.uow import IUoW


class DeleteScheduleEventCase:

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow


    async def excecute(self, id: UUID, user_id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            event = await repository.get_by_id(id=id, user_id=user_id)
            if not event:
                raise ResourceNotFoundError("El evento que desea eliminar no existe")
            if not event.can_delete():
                raise ConflictError("Este evento ya sucedió por lo que no puede borrarse")
            await repository.delete(id)