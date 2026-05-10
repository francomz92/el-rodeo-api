from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.common.application.types import Sentinel


@dataclass
class ScheduleEventCreationValueObject:
    user_id: UUID
    title: str | Sentinel = Sentinel
    description: str | Sentinel = Sentinel
    event_date: date | Sentinel = Sentinel
    pending: bool = True


@dataclass
class ScheduleEventUpdateValueObject:
    user_id: UUID
    title: str | Sentinel = Sentinel
    description: str | Sentinel = Sentinel
    event_date: date | Sentinel = Sentinel


@dataclass
class ScheduleEventsListQueryParamsValueObject:
    title: str | Sentinel = Sentinel
    event_date: date | Sentinel = Sentinel
