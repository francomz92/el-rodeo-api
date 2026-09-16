from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.calendar.domain.constants.calendar_event import CalendarEventType
from src.common.domain.exceptions import BusinessValidationError
from src.common.utils.date_utils import get_current_datetime


class CalendarEventsQueryParams(BaseModel):
    title: str | None = Field(None, max_length=50, description="Title for the event")
    start: datetime = Field(..., description="Start date of event")
    end: datetime = Field(..., description="End date of event")
    order_by: str = Field("start", description="Order by field")
    type: CalendarEventType | None = Field(None, description="Type of event")
    participants: list[UUID] | None = Field(None, description="Participants of the event")
    pending: bool | None = Field(None, description="Status of the event")


class CalendarEventCreationSchema(BaseModel):
    title: str = Field(..., max_length=50, description="Title for the event")
    description: str = Field(..., max_length=255, description="Description about the event")
    start: datetime = Field(..., description="Start date of event")
    end: datetime = Field(..., description="End date of event")
    type: CalendarEventType = Field(..., description="Type of event")
    participants: list[UUID] = Field(..., description="Participants of the event")

    @model_validator(mode="after")
    def validate_event_date(self) -> Self:
        # valildación: inicio de evento no puede ser menor a este instante
        if self.start < get_current_datetime():
            raise BusinessValidationError(
                message="La fecha de inicio no es válida",
                details=[
                    {
                        "field": "start",
                        "message": "La fecha de inicio no puede ser anterior a ahora",
                    }
                ],
            )
        # validación: fin de evento no puede ser menor al inicio
        if self.end < self.start:
            raise BusinessValidationError(
                message="La fecha de fin no es válida",
                details=[
                    {
                        "field": "end",
                        "message": "La fecha de fin no puede ser anterior a la fecha de inicio",
                    }
                ],
            )
        # valicadión: el evento debe tener al menos un participante
        if not self.participants:
            raise BusinessValidationError(
                message="La lista de participantes no puede estar vacía",
                details=[
                    {
                        "field": "participants",
                        "message": "El evento debe tener al menos un participante",
                    }
                ],
            )
        return self


class CalendarEventUpdateSchema(BaseModel):
    title: str = Field(..., max_length=50, description="Title for the event")
    description: str = Field(..., max_length=255, description="Description about the event")
    start: datetime = Field(..., description="Start date of event")
    end: datetime = Field(..., description="End date of event")
    type: CalendarEventType = Field(..., description="Type of event")
    participants: list[UUID] = Field(..., description="Participants of the event")

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        # valildación: inicio de evento no puede ser menor a este instante
        if self.start < get_current_datetime():
            raise BusinessValidationError(
                message="El inicio del evento no es válido",
                details=[
                    {
                        "field": "start",
                        "message": "El inicio del evento no puede ser anterior a ahora",
                    }
                ],
            )
        # validación: fin de evento no puede ser menor al inicio
        if self.end <= self.start:
            raise BusinessValidationError(
                message="El final del evento no es válido",
                details=[
                    {
                        "field": "end",
                        "message": "El final del evento no puede ser anterior o igual al inicio",
                    }
                ],
            )
        # valicadión: el evento debe tener al menos un participante
        if not self.participants:
            raise BusinessValidationError(
                message="La lista de participantes no puede estar vacía",
                details=[
                    {
                        "field": "participants",
                        "message": "El evento debe tener al menos un participante",
                    }
                ],
            )
        return self
