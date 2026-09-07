from uuid import UUID

from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventUpdateValueObject
from src.common.domain.exceptions import BusinessValidationError, ConflictError, NotFoundError


class UpdateScheduleEventService:
    def validate_event_date(self, data: ScheduleEventUpdateValueObject):
        if data.end < data.start:
            raise BusinessValidationError(
                message="Fecha/hora de fin del evento inválido.",
                details=[
                    {
                        "field": "end",
                        "message": "El fin del evento no puede ser anterior al inicio.",
                    }
                ],
            )

    async def validate_event_exists(
        self,
        id: UUID,
        repository: IScheduleEventRepository,
    ):
        event = await repository.get_by_id(id)
        if not event:
            raise NotFoundError("El evento que intenta actualizar no existe.")
        if not event.can_update():
            raise ConflictError("Este evento ya pasó por lo que no se puede editar")

    async def update_event_data(
        self,
        id: UUID,
        data: ScheduleEventUpdateValueObject,
        repository: IScheduleEventRepository,
    ) -> ScheduleEventEntity:
        event = await repository.update_data(id, data)
        await repository.update_participants(event.id, data.participants)
        return event
