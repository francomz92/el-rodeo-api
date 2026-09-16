from uuid import UUID

from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.application.ports.uow import IUoW

from ...services.notifications.calendar_events_reminder_service import CalendarEventsReminderService


class NotifyUpcomingEventsCase:
    def __init__(
        self,
        uow: IUoW,
        service: CalendarEventsReminderService,
        notifier: IEmailNotifier,
    ):
        self.uow = uow
        self.service = service
        self.notifier = notifier

    async def execute(self, tenant_id: UUID | None = None) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(ICalendarEventRepository)
            pending_events = await self.service.get_pending_events(
                repository=repository,
                tenant_id=tenant_id,
            )
            await self.service.send_reminder(self.notifier, repository, pending_events)
