from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository


class RegisterScheduleEventService:
    async def create_new(
        self,
        data,
        repository: IScheduleEventRepository,
    ):
        event = await repository.create(data)
        await repository.add_participants(event.id, data.participants)
        return event
