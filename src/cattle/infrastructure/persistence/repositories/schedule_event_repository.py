from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, delete, exists, insert, select, update

from src.auth.infrastructure.persistence.models import User
from src.cattle.domain.entities.schedule_events_entity import (
    ScheduleEventEntity,
    ScheduleEventRemindedEntity,
)
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.value_objects.schedule_event_value_object import (
    ScheduleEventCreationValueObject,
    ScheduleEventsListQueryParamsValueObject,
    ScheduleEventUpdateValueObject,
)
from src.cattle.infrastructure.persistence.models import ScheduledEvent
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.common.utils.date_utils import get_current_datetime


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
        query = select(
            *ScheduledEvent.__table__.columns,
        ).where(
            ScheduledEvent.id == id,
            ScheduledEvent.user_id == user_id,
        )
        result = await self.db.execute(query)
        event = result.mappings().one_or_none()
        return self._build_schedule_event(event) if event else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: ScheduleEventsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[ScheduleEventEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k in ("title", "event_date"):
                conditions.append(getattr(ScheduledEvent, k) == v)
        query = (
            select(
                *ScheduledEvent.__table__.columns,
            )
            .where(
                ScheduledEvent.user_id == user_id,
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        events = result.mappings().all()
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
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = update(ScheduledEvent).values(**kws)
        await self.db.execute(query)
        return await self.get_by_id(id, data.user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(ScheduledEvent).where(ScheduledEvent.id == id)
        await self.db.execute(query)

    async def get_pending_events(self) -> list[ScheduleEventRemindedEntity]:
        current_date = get_current_datetime().date()
        target_date = current_date + timedelta(days=3)
        query = (
            select(
                ScheduledEvent.title,
                ScheduledEvent.description,
                ScheduledEvent.event_date,
                ScheduledEvent.pending,
                User.name.label("user_name"),
                User.email.label("user_email"),
            )
            .join(ScheduledEvent.user)
            .where(
                ScheduledEvent.pending,
                and_(
                    ScheduledEvent.event_date >= current_date,
                    ScheduledEvent.event_date <= target_date,
                ),
            )
        )
        result = await self.db.execute(query)
        events = result.mappings().all()
        return [
            ScheduleEventRemindedEntity(
                title=event["title"],
                description=event["description"],
                event_date=event["event_date"],
                pending=event["pending"],
                user_name=event["user_name"],
                user_email=event["user_email"],
            )
            for event in events
        ]

    def _build_schedule_event(self, data: RowMapping) -> ScheduleEventEntity:
        return ScheduleEventEntity(
            id=data["id"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            title=data["title"],
            description=data["description"],
            event_date=data["event_date"],
            pending=data["pending"],
        )
