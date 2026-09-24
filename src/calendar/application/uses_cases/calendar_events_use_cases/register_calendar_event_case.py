from uuid import UUID

from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.calendar.domain.constants.calendar_names import MONTHS_NAMES, WEEKLY_DAYS_NAMES
from src.calendar.domain.events.calendar_events import CalendarEventCreated
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.services.calendar_events.register_calendar_event_service import RegisterCalendarEventService
from src.calendar.domain.value_objects.calendar_event_value_object import CalendarEventCreationValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.ports.event_bus import IEventBus
from src.common.utils.date_utils import get_local_from_utc


class RegisterCalendarEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: RegisterCalendarEventService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = service
        self.event_bus = event_bus

    async def execute(self, data: CalendarEventCreationValueObject, tenant_id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(ICalendarEventRepository)
            event = await self.service.create_new(
                data=data,
                repository=repository,
            )
            user_repo = uow.get_repository(IUserRepository)
            users, _, _ = await user_repo.list(tenant_id=tenant_id, ids=data.participants, per_page=len(data.participants))
            start_at = get_local_from_utc(data.start)
            end_at = get_local_from_utc(data.end)
            event_created = CalendarEventCreated(
                aggregate_id=event.id,
                metadata={
                    "tenant_id": str(tenant_id),
                    "title": data.title,
                    "emails": [u.email for u in users],
                    "body": f"""
                        Nuevo evento agendado: {data.title}
                        Fecha: {WEEKLY_DAYS_NAMES[start_at.weekday()]} {start_at.day} de {MONTHS_NAMES[start_at.month]} de {start_at.year}
                        Hora: {start_at.strftime("%H:%M")} - {end_at.strftime("%H:%M")}
                        Descripción:
                            {data.description}
                    """,
                },
            )
            uow.add_outbox_event(event_created)
            await uow.commit()

        await self.event_bus.dispatch(event_created)
        return event
