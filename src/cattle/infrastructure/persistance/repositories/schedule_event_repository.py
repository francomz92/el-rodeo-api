from uuid import UUID

from sqlalchemy import delete, insert, select, update

from src.cattle.application.ports.dtos.schedule_event_dtos import ScheduleEventCreationDTO, ScheduleEventUpdateDTO, ScheduleEventsListQueryParamsDTO
from src.cattle.application.ports.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.cattle.infrastructure.persistance.models import ScheduledEvent
from src.common.application.types import UNSET
from src.common.infrastructure.persistence.connections.db import AsyncSession


class ScheduleEventRepository(IScheduleEventRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID, user_id: UUID) -> ScheduleEventEntity | None:
        query = select(ScheduledEvent).where(
            ScheduledEvent.id == id,
            ScheduledEvent.user_id == user_id,
        )
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        return self._build_schedule_event(event) if event else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsDTO,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[ScheduleEventEntity]:
        query = (
            select(ScheduledEvent)
            .where(ScheduledEvent.user_id == user_id)
            .filter(**vars(filters))
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        events = result.scalars().unique().all()
        return [self._build_schedule_event(event) for event in events]

    async def get_pending_events(self, user_id: UUID) -> list[ScheduleEventEntity]:
        query = select(ScheduledEvent).where(
            ScheduledEvent.user_id == user_id,
            ScheduledEvent.pending == True,
        )
        result = await self.db.execute(query)
        events = result.scalars().unique().all()
        return [self._build_schedule_event(event) for event in events]

    async def create(self, data: ScheduleEventCreationDTO) -> ScheduleEventEntity:
        query = insert(ScheduledEvent).values(vars(data)).returning(ScheduledEvent.id)
        result = await self.db.execute(query)
        event_id = result.scalar_one()
        return await self.get_by_id(event_id, data.user_id)  # type: ignore

    async def update_data(self, id: UUID, data: ScheduleEventUpdateDTO) -> ScheduleEventEntity:
        kws = {k: v for k, v in vars(data).items() if v != UNSET}
        query = update(ScheduledEvent).values(**kws)
        await self.db.execute(query)
        return await self.get_by_id(id, data.user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(ScheduledEvent).where(ScheduledEvent.id == id)
        await self.db.execute(query)

    def _build_schedule_event(self, data: ScheduledEvent) -> ScheduleEventEntity:
        return ScheduleEventEntity(
            id=data.id,
            user_id=data.user_id,
            created_at=data.created_at,
            title=data.title,
            description=data.description,
            event_date=data.event_date,
            pending=data.pending,
        )
