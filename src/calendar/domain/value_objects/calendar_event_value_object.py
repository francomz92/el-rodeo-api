from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.calendar.domain.constants.calendar_event import CalendarEventType
from src.common.domain.types import Sentinel


@dataclass
class CalendarEventCreationValueObject:
    user_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    type: CalendarEventType
    participants: list[UUID]
    pending: bool = True


@dataclass
class CalendarEventUpdateValueObject:
    user_id: UUID
    title: str
    description: str
    start: datetime
    end: datetime
    type: CalendarEventType
    participants: list[UUID]


@dataclass
class CalendarEventsListQueryParamsValueObject:
    title: str | Sentinel = Sentinel.UNSET
    start: datetime | Sentinel = Sentinel.UNSET
    end: datetime | Sentinel = Sentinel.UNSET
    type: CalendarEventType | Sentinel = Sentinel.UNSET
    participants: list[UUID] | Sentinel = Sentinel.UNSET
    pending: bool | Sentinel = Sentinel.UNSET
