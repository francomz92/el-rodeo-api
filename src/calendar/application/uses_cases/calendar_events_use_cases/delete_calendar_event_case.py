from uuid import UUID

from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.services.calendar_events.delete_calendar_event_service import DeleteCalendarEventService
from src.common.application.ports.uow import IUoW


class DeleteCalendarEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeleteCalendarEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(ICalendarEventRepository)
            await self.service.validate_for_delete(
                id=id,
                repository=repository,
            )
            await self.service.delete_event(
                id=id,
                repository=repository,
            )
            await uow.commit()
