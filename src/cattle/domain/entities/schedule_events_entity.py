from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class ScheduleEventEntity:
    id: UUID
    user_id: UUID
    created_at: datetime
    title: str
    description: str
    event_date: date
    pending: bool

    def can_update(self) -> bool:
        return self.pending

    def can_delete(self) -> bool:
        return self.pending


@dataclass
class ScheduleEventRemindedEntity:
    user_name: str
    user_email: str
    title: str
    description: str
    event_date: date
    pending: bool
