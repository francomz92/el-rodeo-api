from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from src.common.application.types import UNSET


@dataclass
class ScheduleEventCreationDTO:
    user_id: UUID
    title: str | UNSET = UNSET
    description: str | UNSET = UNSET
    event_date: date | UNSET = UNSET
    pending: bool = True


@dataclass
class ScheduleEventUpdateDTO:
    user_id: UUID
    title: str | UNSET = UNSET
    description: str | UNSET = UNSET
    event_date: date | UNSET = UNSET


@dataclass
class ScheduleEventsListQueryParamsDTO:
    title: str | UNSET = UNSET
    event_date: date | UNSET = UNSET