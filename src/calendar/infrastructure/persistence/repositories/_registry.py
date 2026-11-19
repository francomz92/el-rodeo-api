from src.calendar.domain.repositories.gdpr_data_repository_port import (
    ICalendarGDPRDataRepository,
)
from src.calendar.infrastructure.persistence.repositories.calendar_event_repository import CalendarEventRepository, ICalendarEventRepository
from src.calendar.infrastructure.persistence.repositories.gdpr_data_repository import CalendarGDPRDataRepository
from src.common.domain.repository import IRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    ICalendarEventRepository: CalendarEventRepository,
    ICalendarGDPRDataRepository: CalendarGDPRDataRepository,
}
