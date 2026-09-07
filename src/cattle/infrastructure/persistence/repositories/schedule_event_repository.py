from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, delete, exists, func, insert, select, update

from src.auth.infrastructure.persistence.models import User
from src.cattle.domain.entities.schedule_events_entity import (
    ScheduleEventEntity,
    ScheduleEventParticipantEntity,
    ScheduleEventRemindedEntity,
    ScheduleEventRemindedParticipantEntity,
)
from src.cattle.domain.repositories.schedule_events_repository_port import IScheduleEventRepository
from src.cattle.domain.value_objects.schedule_event_value_object import (
    ScheduleEventCreationValueObject,
    ScheduleEventsListQueryParamsValueObject,
    ScheduleEventUpdateValueObject,
)
from src.cattle.infrastructure.persistence.models import ScheduledEvent
from src.cattle.infrastructure.persistence.models._schedule_event_models import ScheduledEventParticipant
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
                func.coalesce(
                    func.json_agg(
                        func.json_build_object(
                            "id",
                            User.id,
                            "name",
                            User.name,
                        )
                    ).filter(User.id.is_not(None)),
                    func.json_build_array(),
                ).label("participants"),
            )
            .where(ScheduledEvent.id == id)
            .outerjoin(ScheduledEventParticipant, ScheduledEventParticipant.event_id == id)
            .outerjoin(User, User.id == ScheduledEventParticipant.user_id)
            .select_from(ScheduledEvent)
            .group_by(ScheduledEvent.id)
        )
        result = await self.db.execute(query)
        event = result.mappings().one_or_none()
        return self._build_schedule_event(event) if event else None

    async def list_for_user(self, filters: ScheduleEventsListQueryParamsValueObject, order_by: str) -> list[ScheduleEventEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "title":
                conditions.append(ScheduledEvent.title.ilike(f"%{v}%"))
            elif k == "start":
                conditions.append(ScheduledEvent.start >= v)
            elif k == "end":
                conditions.append(ScheduledEvent.end <= v)
            elif k == "participants":
                conditions.append(ScheduledEventParticipant.user_id.in_(v))
            elif k in ("type", "pending"):
                conditions.append(getattr(ScheduledEvent, k) == v)
        query = self._filter_tenant(
            select(
                *ScheduledEvent.__table__.columns,
                func.coalesce(
                    func.json_agg(
                        func.json_build_object(
                            "id",
                            User.id,
                            "name",
                            User.name,
                        )
                    ).filter(User.id.is_not(None)),
                    func.json_build_array(),
                ).label("participants"),
            )
            .where(*conditions)
            .outerjoin(ScheduledEventParticipant, ScheduledEventParticipant.event_id == ScheduledEvent.id)
            .outerjoin(User, User.id == ScheduledEventParticipant.user_id)
            .group_by(ScheduledEvent.id)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        events = result.mappings().all()
        return [self._build_schedule_event(event) for event in events]

    async def create(
        self,
        data: ScheduleEventCreationValueObject,
    ) -> ScheduleEventEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET and k != "participants"}
        query = (
            insert(ScheduledEvent)
            .values(
                **kws,
                tenant_id=self._tenant_id,
            )
            .returning(ScheduledEvent.id)
        )
        result = await self.db.execute(query)
        event_id = result.scalar_one()
        new_entity = await self.get_by_id(event_id)
        self._audit_create("schedule_event", event_id, kws)
        return new_entity  # type: ignore

    async def add_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        query = insert(ScheduledEventParticipant).values([{"event_id": event_id, "user_id": participant} for participant in participants])
        await self.db.execute(query)

    async def update_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        old_row = await self.db.execute(
            self._filter_tenant(
                select(ScheduledEventParticipant.user_id).where(ScheduledEventParticipant.event_id == event_id),
            )
        )
        old_participants = old_row.mappings().all()
        query = delete(ScheduledEventParticipant).where(ScheduledEventParticipant.event_id == event_id)
        await self.db.execute(query)
        query = insert(ScheduledEventParticipant).values([{"event_id": event_id, "user_id": participant} for participant in participants])
        await self.db.execute(query)
        self._audit_update(
            "schedule_event_participant",
            event_id,
            old_values={"participants": old_participants},
            new_values={"participants": participants},
        )

    async def update_data(
        self,
        id: UUID,
        data: ScheduleEventUpdateValueObject,
    ) -> ScheduleEventEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(ScheduledEvent.__table__).where(ScheduledEvent.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET and k != "user_id" and k != "participants"}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(ScheduledEvent).values(**kws).where(ScheduledEvent.id == id))
        await self.db.execute(query)
        new_entity = await self.get_by_id(id)
        self._audit_update("schedule_event", id, old_values, kws)
        return new_entity  # type: ignore

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
                ScheduledEvent.id,
                ScheduledEvent.title,
                ScheduledEvent.description,
                ScheduledEvent.pending,
                ScheduledEvent.tenant_id,
                func.coalesce(
                    func.json_agg(
                        func.json_build_object(
                            "name",
                            User.name,
                            "email",
                            User.email,
                        )
                    ).filter(User.id.is_not(None)),
                    func.json_build_array(),
                ).label("participants"),
            )
            .outerjoin(ScheduledEventParticipant, ScheduledEventParticipant.event_id == ScheduledEvent.id)
            .outerjoin(User, User.id == ScheduledEventParticipant.user_id)
            .where(
                ScheduledEvent.pending,
                and_(
                    ScheduledEvent.start >= current_date,
                    ScheduledEvent.end <= target_date,
                ),
            )
            .group_by(ScheduledEvent.id)
        )
        if tenant_id is not None:
            query = query.where(ScheduledEvent.tenant_id == tenant_id)
        result = await self.db.execute(query)
        events = result.mappings().all()
        return [
            ScheduleEventRemindedEntity(
                event_id=event["id"],
                title=event["title"],
                description=event["description"],
                start=event["start"],
                end=event["end"],
                pending=event["pending"],
                participants=[
                    ScheduleEventRemindedParticipantEntity(
                        name=participant["name"],
                        email=participant["email"],
                    )
                    for participant in event["participants"]
                ],
            )
            for event in events
        ]

    async def mark_as_notified(self, event_id: UUID) -> None:
        query = self._filter_tenant(
            update(ScheduledEvent).values(pending=False, updated_at=func.now()).where(ScheduledEvent.id == event_id)
        )
        await self.db.execute(query)

    def _build_schedule_event(self, data: RowMapping) -> ScheduleEventEntity:
        return ScheduleEventEntity(
            id=data["id"],
            tenant_id=data["tenant_id"],
            user_id=data["user_id"],
            created_at=data["created_at"],
            title=data["title"],
            description=data["description"],
            start=data["start"],
            end=data["end"],
            pending=data["pending"],
            type=data["type"],
            participants=[
                ScheduleEventParticipantEntity(
                    id=participant["id"],
                    name=participant["name"],
                )
                for participant in data["participants"]
            ],
        )
