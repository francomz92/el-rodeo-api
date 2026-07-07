from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, delete, exists, func, insert, select, update

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
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.common.utils.date_utils import get_current_datetime


class ScheduleEventRepository(IScheduleEventRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[ScheduledEvent] = ScheduledEvent

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(ScheduledEvent).where(ScheduledEvent.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> ScheduleEventEntity | None:
        query = self._filter_tenant(
            select(
                *ScheduledEvent.__table__.columns,
            ).where(ScheduledEvent.id == id)
        )
        result = await self.db.execute(query)
        event = result.mappings().one_or_none()
        return self._build_schedule_event(event) if event else None

    async def list_for_user(
        self,
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
        query = self._filter_tenant(
            select(
                *ScheduledEvent.__table__.columns,
            )
            .where(*conditions)
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
                tenant_id=self._tenant_id,
            )
            .returning(ScheduledEvent.id)
        )
        result = await self.db.execute(query)
        event_id = result.scalar_one()
        new_entity = await self.get_by_id(event_id)
        self._audit_create("schedule_event", event_id, vars(data))
        return new_entity  # type: ignore[return-value]

    async def update_data(
        self,
        id: UUID,
        data: ScheduleEventUpdateValueObject,
    ) -> ScheduleEventEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(ScheduledEvent.__table__).where(ScheduledEvent.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(ScheduledEvent).values(**kws).where(ScheduledEvent.id == id))
        await self.db.execute(query)
        new_entity = await self.get_by_id(id)
        self._audit_update("schedule_event", id, old_values, vars(data))
        return new_entity  # type: ignore[return-value]

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(ScheduledEvent.__table__).where(ScheduledEvent.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(ScheduledEvent).where(ScheduledEvent.id == id))
        await self.db.execute(query)
        self._audit_delete("schedule_event", id, old_values)

    async def get_pending_events(self, tenant_id: UUID | None = None) -> list[ScheduleEventRemindedEntity]:
        current_date = get_current_datetime().date()
        target_date = current_date + timedelta(days=3)
        query = (
            select(
                ScheduledEvent.title,
                ScheduledEvent.description,
                ScheduledEvent.event_date,
                ScheduledEvent.pending,
                ScheduledEvent.tenant_id,
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
        if tenant_id is not None:
            query = query.where(ScheduledEvent.tenant_id == tenant_id)
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
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            title=data["title"],
            description=data["description"],
            event_date=data["event_date"],
            pending=data["pending"],
        )
