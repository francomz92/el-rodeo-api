from uuid import UUID

from src.common.domain.exceptions import BusinessValidationError, ConflictError, NotFoundError

from ...entities.calendar_event_entity import CalendarEventEntity
from ...repositories.calendar_events_repository_port import ICalendarEventRepository
from ...value_objects.calendar_event_value_object import CalendarEventUpdateValueObject


class UpdateCalendarEventService:
    def validate_event_date(self, data: CalendarEventUpdateValueObject):
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
        repository: ICalendarEventRepository,
    ):
        event = await repository.get_by_id(id)
        if not event:
            raise NotFoundError("El evento que intenta actualizar no existe.")
        if not event.can_update():
            raise ConflictError("Este evento ya pasó por lo que no se puede editar")

    async def update_event_data(
        self,
        id: UUID,
        data: CalendarEventUpdateValueObject,
        repository: ICalendarEventRepository,
    ) -> CalendarEventEntity:
        event = await repository.update_data(id, data)
        await repository.update_participants(event.id, data.participants)
        return event
