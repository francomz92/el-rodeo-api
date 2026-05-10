from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update

from src.cattle.domain.entities.schedule_events_entity import ScheduleEventEntity
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.value_objects.schedule_event_value_object import (
    ScheduleEventCreationValueObject,
    ScheduleEventsListQueryParamsValueObject,
    ScheduleEventUpdateValueObject,
)
from src.cattle.infrastructure.persistance.models import ScheduledEvent
from src.common.application.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class ScheduleEventRepository(IScheduleEventRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(ScheduledEvent)
            .where(
                ScheduledEvent.id == id,
                ScheduledEvent.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> ScheduleEventEntity | None:
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
        filters: ScheduleEventsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[ScheduleEventEntity]:
        kws = {k: v for k, v in vars(filters).items() if v != Sentinel.UNSET}
        query = (
            select(ScheduledEvent)
            .where(
                ScheduledEvent.user_id == user_id,
            )
            .filter_by(**kws)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        events = result.scalars().unique().all()
        return [self._build_schedule_event(event) for event in events]

    async def get_pending_events(
        self,
        user_id: UUID,
    ) -> list[ScheduleEventEntity]:
        query = select(ScheduledEvent).where(
            ScheduledEvent.user_id == user_id,
            ScheduledEvent.pending,  # == True
        )
        result = await self.db.execute(query)
        events = result.scalars().unique().all()
        return [self._build_schedule_event(event) for event in events]

    async def create(
        self,
        data: ScheduleEventCreationValueObject,
    ) -> ScheduleEventEntity:
        query = (
            insert(ScheduledEvent)
            .values(
                **vars(data),
            )
            .returning(ScheduledEvent.id)
        )
        result = await self.db.execute(query)
        event_id = result.scalar_one()
        return await self.get_by_id(event_id, data.user_id)  # type: ignore

    async def update_data(
        self,
        id: UUID,
        data: ScheduleEventUpdateValueObject,
    ) -> ScheduleEventEntity:
        kws = {k: v for k, v in vars(data).items() if v != Sentinel.UNSET}
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
