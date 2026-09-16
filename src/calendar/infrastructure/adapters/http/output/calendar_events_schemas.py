from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.calendar.domain.constants.calendar_event import CalendarEventType


class CalendarEventParticipantSchema(BaseModel):
    id: UUID
    name: str


class CalendarEventSchema(BaseModel):
    id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    type: CalendarEventType
    participants: list[CalendarEventParticipantSchema]

    model_config = ConfigDict(from_attributes=True)
