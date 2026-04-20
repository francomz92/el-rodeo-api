from uuid import UUID

from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventsListQueryParamsDTO
from src.cattle.application.ports.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.common.application.ports.uow import IUoW


class ListScheduleEventsCase:

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow


    async def excecute(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsDTO,
        limit: int,
        offset: int,
        order_by: str,
    ):
        async with self.uow as uow:
            repository = uow.get_repository(IScheduleEventRepository)
            return await repository.list_for_user(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )