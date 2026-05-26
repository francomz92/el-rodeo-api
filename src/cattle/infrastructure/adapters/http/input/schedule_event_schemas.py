from datetime import date
from typing import Self

from pydantic import BaseModel, Field, model_validator

from src.common.infrastructure.adapters.http.input.query_params import StandardQueryParams
from src.common.utils.date_utils import get_current_datetime


class ScheduleEventsQueryParams(StandardQueryParams):
    title: str | None = Field(None, max_length=50, description="Title for the event")
    event_date: date | None = Field(None, description="Date of event")


class ScheduleEventCreationSchema(BaseModel):
    title: str = Field(..., max_length=50, description="Title for the event")
    description: str = Field(..., max_length=255, description="Description about the event")
    event_date: date = Field(..., description="Date of event")

    @model_validator(mode="after")
    def validate_event_date(self) -> Self:
        if self.event_date < get_current_datetime().date():
            raise ValueError("La fecha seleccionada no puede ser menor a hoy")
        return self


class ScheduleEventUpdateSchema(BaseModel):
    title: str = Field(..., max_length=50, description="Title for the event")
    description: str = Field(..., max_length=255, description="Description about the event")
    event_date: date = Field(..., description="Date of event")

    @model_validator(mode="after")
    def validate_event_date(self) -> Self:
        if self.event_date < get_current_datetime().date():
            raise ValueError("La fecha seleccionada no puede ser menor a hoy")
        return self
