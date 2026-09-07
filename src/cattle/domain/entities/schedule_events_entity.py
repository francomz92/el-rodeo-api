from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.cattle.domain.constants.animal_scheduled_event import AnimalEventType


@dataclass
class ScheduleEventParticipantEntity:
    id: UUID
    name: str


@dataclass
class ScheduleEventEntity:
    id: UUID
    tenant_id: UUID
    user_id: UUID
    created_at: datetime
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    type: AnimalEventType
    participants: list[ScheduleEventParticipantEntity]

    def can_update(self) -> bool:
        return self.pending

    def can_delete(self) -> bool:
        return self.pending


@dataclass
class ScheduleEventRemindedParticipantEntity:
    name: UUID
    email: str


@dataclass
class ScheduleEventRemindedEntity:
    event_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    pending: bool
    participants: list[ScheduleEventRemindedParticipantEntity]
