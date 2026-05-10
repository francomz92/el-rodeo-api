from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.domain.exceptions import ConflictError, NotFoundError


class DeleteScheduleEventService:
    async def validate_for_delete(
        self,
        id: UUID,
        user_id: UUID,
        repository: IScheduleEventRepository,
    ):
        event = await repository.get_by_id(id, user_id)
        if not event:
            raise NotFoundError("El evento que intenta eliminar no existe.")
        if not event.can_delete():
            raise ConflictError("No se puede eliminar porque el evento ya finalizo.")

    async def delete_event(
        self,
        id: UUID,
        repository: IScheduleEventRepository,
    ):
        await repository.delete(id=id)
