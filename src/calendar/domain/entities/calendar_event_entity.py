from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..constants.calendar_event import CalendarEventType


@dataclass
class CalendarEventParticipantEntity:
    id: UUID
    name: str


@dataclass
class CalendarEventEntity:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    created_at: datetime
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    type: CalendarEventType
    participants: list[CalendarEventParticipantEntity]

    def can_update(self) -> bool:
        return self.pending

    def can_delete(self) -> bool:
        return self.pending


@dataclass
class CalendarEventRemindedParticipantEntity:
    name: UUID
    email: str


@dataclass
class CalendarEventRemindedEntity:
    event_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    participants: list[CalendarEventRemindedParticipantEntity]
