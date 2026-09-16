from ...repositories.calendar_events_repository_port import ICalendarEventRepository


class RegisterCalendarEventService:
    async def create_new(
        self,
        data,
        repository: ICalendarEventRepository,
    ):
        event = await repository.create(data)
        await repository.add_participants(event.id, data.participants)
        return event
