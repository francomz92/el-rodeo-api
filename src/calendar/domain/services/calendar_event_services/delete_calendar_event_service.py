from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError

from ...repositories.calendar_events_repository_port import ICalendarEventRepository


class DeleteCalendarEventService:
    async def validate_for_delete(
        self,
        id: UUID,
        repository: ICalendarEventRepository,
    ):
        event = await repository.get_by_id(id)
        if not event:
            raise NotFoundError("El evento que intenta eliminar no existe.")
        if not event.can_delete():
            raise ConflictError("No se puede eliminar porque el evento ya finalizo.")

    async def delete_event(
        self,
        id: UUID,
        repository: ICalendarEventRepository,
    ):
        await repository.delete(id=id)
