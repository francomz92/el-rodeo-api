from datetime import date
from typing import Any
from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.domain.exceptions import BusinessValidationError, ConflictError, NotFoundError
from src.common.utils.date_utils import get_current_datetime


class UpdateScheduleEventService:
    def validate_event_date(
        self,
        event_date: date | Any,
    ):
        if not isinstance(event_date, date):
            raise BusinessValidationError(
                message="La fecha del evento no es válida.",
                details=[
                    {
                        "field": "event_date",
                        "message": "La fecha del evento debe ser una fecha válida.",
                    }
                ],
            )
        if event_date < get_current_datetime().date():
            raise BusinessValidationError(
                message="La fecha del evento ya ha pasado.",
                details=[
                    {
                        "field": "event_date",
                        "message": "La fecha del evento no puede ser menor a la fecha actual.",
                    }
                ],
            )

    async def validate_event_exists(
        self,
        id: UUID,
        user_id: UUID,
        repository: IScheduleEventRepository,
    ):
        event = await repository.get_by_id(id, user_id)
        if not event:
            raise NotFoundError("El evento que intenta actualizar no existe.")
        if not event.can_update():
            raise ConflictError("Este evento ya pasó por lo que no se puede editar")

    async def update_event_data(
        self,
        id: UUID,
        data,
        repository: IScheduleEventRepository,
    ):
        return await repository.update_data(id, data)
