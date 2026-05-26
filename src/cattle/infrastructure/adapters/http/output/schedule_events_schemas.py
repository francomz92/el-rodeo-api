from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ScheduleEventSchema(BaseModel):
    id: UUID
    title: str
    description: str
    event_date: date
