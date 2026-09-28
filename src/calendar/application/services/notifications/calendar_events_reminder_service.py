from typing import cast
from uuid import UUID

from src.calendar.domain.entities.calendar_event_entity import CalendarEventRemindedEntity, CalendarEventRemindedParticipantEntity
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.repositories.calendar_user_projection_port import ICalendarUserProjectionReader
from src.common.application.ports.email_notifier import IEmailNotifier
from src.common.utils.date_utils import get_local_from_utc


class CalendarEventsReminderService:
    async def get_pending_events(
        self,
        repository: ICalendarEventRepository,
        user_reader: ICalendarUserProjectionReader,
        tenant_id: UUID | None = None,
    ) -> list[CalendarEventRemindedEntity]:
        events = await repository.get_pending_events(tenant_id=tenant_id)
        user_ids = {user_id for event in events for user_id in event.participant_user_ids}
        users_by_id = await user_reader.get_users_by_ids(user_ids)
        for event in events:
            event.participants = [
                CalendarEventRemindedParticipantEntity(
                    name=cast(UUID, users_by_id[user_id].name),
                    email=users_by_id[user_id].email,
                )
                for user_id in event.participant_user_ids
                if user_id in users_by_id
            ]
        return events

    def send_reminder(
        self,
        notifier: IEmailNotifier,
        pending_events: list[CalendarEventRemindedEntity],
    ):
        for event in pending_events:
            start_at = get_local_from_utc(event.start)
            end_at = get_local_from_utc(event.end)
            notifier.send(
                to=[participant.email for participant in event.participants],
                subject=f"Proximo evento: {event.title}",
                body=f"""
                El siguiente evento esta muy cerca:\n{event.title}
                \n
                Inicio: {start_at.date()} a las {start_at.hour}:{start_at.minute}
                \n
                Fin: {end_at.date()} a las {end_at.hour}:{end_at.minute}
                \n\n
                Descripción: {event.description}\n
                """,
            )
