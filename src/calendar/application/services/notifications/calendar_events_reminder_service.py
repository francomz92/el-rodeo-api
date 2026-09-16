from uuid import UUID

from src.calendar.domain.entities.calendar_event_entity import CalendarEventRemindedEntity
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.common.application.ports.email_notifier import IEmailNotifier


class CalendarEventsReminderService:
    async def get_pending_events(
        self,
        repository: ICalendarEventRepository,
        tenant_id: UUID | None = None,
    ) -> list[CalendarEventRemindedEntity]:
        return await repository.get_pending_events(tenant_id=tenant_id)

    async def send_reminder(
        self,
        notifier: IEmailNotifier,
        repository: ICalendarEventRepository,
        pending_events: list[CalendarEventRemindedEntity],
    ):
        for event in pending_events:
            notifier.send(
                to=[participant.email for participant in event.participants],
                subject=f"Proximo evento: {event.title}",
                body=f"""
                El siguiente evento esta muy cerca:\n{event.title}
                \n
                Inicio: {event.start.date()} a las {event.start.hour}:{event.start.minute}
                \n
                Fin: {event.end.date()} a las {event.end.hour}:{event.end.minute}
                \n\n
                Descripción: {event.description}\n
                """,
            )
            await repository.mark_as_notified(event.event_id)
