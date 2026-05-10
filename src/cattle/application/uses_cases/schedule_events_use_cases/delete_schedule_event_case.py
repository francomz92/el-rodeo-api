from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.services.schedule_events.delete_schedule_event_service import DeleteScheduleEventService
from src.common.application.ports.uow import IUoW


class DeleteScheduleEventCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeleteScheduleEventService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            await self.service.validate_for_delete(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await self.service.delete_event(
                id=id,
                repository=repository,
            )
            await uow.commit()
