from src.calendar.domain.repositories.gdpr_data_repository_port import (
    ICalendarGDPRDataRepository,
)
from src.common.domain.repository import IRepository

from .calendar_event_repository import (
    CalendarEventRepository,
    ICalendarEventRepository,
)
from .gdpr_data_repository import CalendarGDPRDataRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    ICalendarEventRepository: CalendarEventRepository,
    ICalendarGDPRDataRepository: CalendarGDPRDataRepository,
}
