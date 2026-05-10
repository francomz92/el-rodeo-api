from datetime import date
from typing import Any

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.domain.exceptions import BusinessValidationError
from src.common.utils.date_utils import get_current_datetime


class RegisterScheduleEventService:
    def validate_event_date(
        self,
        event_date: date | Any,
    ):
        if not isinstance(event_date, date):
            raise BusinessValidationError(
                message="La fecha del evento es requerida.",
                details=[
                    {
                        "field": "event_date",
                        "message": "La fecha de inicio es requerida.",
                    }
                ],
            )
        if event_date > get_current_datetime().date():
            raise BusinessValidationError(
                message="La fecha del evento ya ha pasado.",
                details=[
                    {
                        "field": "event_date",
                        "message": "La fecha del evento no puede ser menor a la fecha actual.",
                    }
                ],
            )

    async def create_new(
        self,
        data,
        repository: IScheduleEventRepository,
    ):
        return await repository.create(data)
