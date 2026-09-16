from src.common.domain.repository import IRepository

from .calendar_event_repository import (
    CalendarEventRepository,
    ICalendarEventRepository,
)

repositories_list: dict[type[IRepository], type[IRepository]] = {
    ICalendarEventRepository: CalendarEventRepository,
}
