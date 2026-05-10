from uuid import UUID

from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository


class ListScheduleEventService:
    async def get_events(
        self,
        user_id: UUID,
        query,
        limit: int,
        offset: int,
        order_by: str,
        repository: IScheduleEventRepository,
    ):
        events_list = await repository.list_for_user(
            user_id=user_id,
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return events_list
