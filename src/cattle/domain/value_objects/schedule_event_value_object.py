from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.cattle.domain.constants.animal_scheduled_event import AnimalEventType
from src.common.domain.types import Sentinel


@dataclass
class ScheduleEventCreationValueObject:
    user_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    type: AnimalEventType
    participants: list[UUID]
    pending: bool = True


@dataclass
class ScheduleEventUpdateValueObject:
    user_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    type: AnimalEventType
    participants: list[UUID]


@dataclass
class ScheduleEventsListQueryParamsValueObject:
    title: str | Sentinel = Sentinel.UNSET
    start: datetime | Sentinel = Sentinel.UNSET
    end: datetime | Sentinel = Sentinel.UNSET
    type: AnimalEventType | Sentinel = Sentinel.UNSET
    participants: list[UUID] | Sentinel = Sentinel.UNSET
    pending: bool | Sentinel = Sentinel.UNSET
