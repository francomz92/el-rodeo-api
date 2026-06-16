from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ScheduleEventSchema(BaseModel):
    id: UUID
    title: str
    description: str
    event_date: date

    model_config = ConfigDict(from_attributes=True)
