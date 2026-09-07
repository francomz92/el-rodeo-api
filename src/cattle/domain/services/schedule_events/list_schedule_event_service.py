from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.value_objects.schedule_event_value_object import ScheduleEventsListQueryParamsValueObject


class ListScheduleEventService:
    async def get_events(
        self,
        query: ScheduleEventsListQueryParamsValueObject,
        order_by: str,
        repository: IScheduleEventRepository,
    ) -> list[ScheduleEventEntity]:
        events_list = await repository.list_for_user(
            filters=query,
            order_by=order_by,
        )
        return events_list
