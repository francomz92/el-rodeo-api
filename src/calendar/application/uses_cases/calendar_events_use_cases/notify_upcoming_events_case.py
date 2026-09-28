from uuid import UUID

from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.repositories.calendar_user_projection_port import ICalendarUserProjectionReader
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
            user_reader = uow.get_repository(ICalendarUserProjectionReader)
            pending_events = await self.service.get_pending_events(
                repository=repository,
                user_reader=user_reader,
                tenant_id=tenant_id,
            )
            self.service.send_reminder(self.notifier, pending_events)
            for event in pending_events:
                await repository.mark_as_notified(event.event_id)
