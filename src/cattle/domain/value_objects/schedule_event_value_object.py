from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.common.domain.types import Sentinel


@dataclass
class ScheduleEventCreationValueObject:
    user_id: UUID
    title: str | Sentinel = Sentinel.UNSET
    description: str | Sentinel = Sentinel.UNSET
    event_date: date | Sentinel = Sentinel.UNSET
    pending: bool = True


@dataclass
class ScheduleEventUpdateValueObject:
    user_id: UUID
    title: str | Sentinel = Sentinel.UNSET
    description: str | Sentinel = Sentinel.UNSET
    event_date: date | Sentinel = Sentinel.UNSET


@dataclass
class ScheduleEventsListQueryParamsValueObject:
    title: str | Sentinel = Sentinel.UNSET
    event_date: date | Sentinel = Sentinel.UNSET
