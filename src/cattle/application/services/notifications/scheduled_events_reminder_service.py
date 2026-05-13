from src.cattle.domain.entities.schedule_events_entity import ScheduleEventRemindedEntity
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.ports.email_notifier import IEmailNotifier


class ScheduledEventsReminderService:
    async def get_pending_events(
        self,
        repository: IScheduleEventRepository,
    ) -> list[ScheduleEventRemindedEntity]:
        return await repository.get_pending_events()

    def send_reminder(
        self,
        notifier: IEmailNotifier,
        repository: IScheduleEventRepository,
        pending_events: list[ScheduleEventRemindedEntity],
    ):
        for event in pending_events:
            notifier.send(
                to=[event.user_email],
                subject=f"Proximo evento: {event.title}",
                body=f"""
                El siguiente evento esta muy cerca:\n{event.title} - {event.event_date}\n\n
                Descripción: {event.description}\n
                """,
            )
