from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.cattle.domain.constants.animal_scheduled_event import AnimalEventType


class ScheduleEventParticipantSchema(BaseModel):
    id: UUID
    name: str


class ScheduleEventSchema(BaseModel):
    id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    type: AnimalEventType
    participants: list[ScheduleEventParticipantSchema]

    model_config = ConfigDict(from_attributes=True)
