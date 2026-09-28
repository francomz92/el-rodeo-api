from uuid import UUID

from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.calendar.domain.constants.calendar_names import MONTHS_NAMES, WEEKLY_DAYS_NAMES
from src.calendar.domain.entities.calendar_event_entity import CalendarEventParticipantEntity
from src.calendar.domain.events.calendar_events import CalendarEventUpdated
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.repositories.calendar_user_projection_port import ICalendarUserProjectionReader
from src.calendar.domain.services.calendar_events.update_calendar_event_service import UpdateCalendarEventService
from src.calendar.domain.value_objects.calendar_event_value_object import CalendarEventUpdateValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus
from src.common.utils.date_utils import get_local_from_utc


class UpdateCalendarEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateCalendarEventService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, id: UUID, data: CalendarEventUpdateValueObject, tenant_id: UUID):
        async with self.uow as uow:
            self.service.validate_event_date(data)
            repository = uow.get_repository(ICalendarEventRepository)
            await self.service.validate_event_exists(
                id=id,
                repository=repository,
            )
            schedule_event = await self.service.update_event_data(
                id=id,
                data=data,
                repository=repository,
            )
            user_reader = uow.get_repository(ICalendarUserProjectionReader)
            users_by_id = await user_reader.get_users_by_ids(set(schedule_event.participant_user_ids))
            schedule_event.participants = [
                CalendarEventParticipantEntity(id=user_id, name=users_by_id[user_id].name)
                for user_id in schedule_event.participant_user_ids
                if user_id in users_by_id
            ]
            user_repo = uow.get_repository(IUserRepository)
            users, _, _ = await user_repo.list(tenant_id=tenant_id, ids=data.participants, per_page=len(data.participants))
            start_at = get_local_from_utc(data.start)
            end_at = get_local_from_utc(data.end)
            event_updated = CalendarEventUpdated(
                aggregate_id=id,
                metadata={
                    "tenant_id": str(tenant_id),
                    "title": data.title,
                    "emails": [u.email for u in users],
                    "body": f"""
                        Evento actualizado: {data.title}
                        Fecha: {WEEKLY_DAYS_NAMES[start_at.weekday()]} {start_at.day} de {MONTHS_NAMES[start_at.month]} de {start_at.year}
                        Hora: {start_at.strftime("%H:%M")} - {end_at.strftime("%H:%M")}
                        Descripción:
                            {data.description}
                    """,
                },
            )
            uow.add_outbox_event(event_updated)
            await uow.commit()

        await self.event_bus.dispatch(event_updated)
        return schedule_event
