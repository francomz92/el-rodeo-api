from src.cattle.application.services.notifications.scheduled_events_reminder_service import ScheduledEventsReminderService
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.application.ports.uow import IUoW


class NotifyUpcomingEventsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ScheduledEventsReminderService,
        notifier: IEmailNotifier,
    ):
        self.uow = uow
        self.service = service
        self.notifier = notifier

    async def execute(self) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            pending_events = await self.service.get_pending_events(repository)
            self.service.send_reminder(self.notifier, repository, pending_events)
