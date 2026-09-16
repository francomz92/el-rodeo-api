from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, delete, exists, func, insert, select, update

from src.auth.infrastructure.persistence.models import User
from src.calendar.domain.entities.calendar_event_entity import (
    CalendarEventEntity,
    CalendarEventParticipantEntity,
    CalendarEventRemindedEntity,
    CalendarEventRemindedParticipantEntity,
)
from src.calendar.domain.repositories.calendar_events_repository_port import ICalendarEventRepository
from src.calendar.domain.value_objects.calendar_event_value_object import (
    CalendarEventCreationValueObject,
    CalendarEventsListQueryParamsValueObject,
    CalendarEventUpdateValueObject,
)
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.common.utils.date_utils import get_current_datetime

from ..models import CalendarEvent, CalendarEventParticipant


class CalendarEventRepository(ICalendarEventRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[CalendarEvent] = CalendarEvent

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(CalendarEvent).where(CalendarEvent.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> CalendarEventEntity | None:
        query = self._filter_tenant(
            select(
                *CalendarEvent.__table__.columns,
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
            .where(CalendarEvent.id == id)
            .outerjoin(CalendarEventParticipant, CalendarEventParticipant.event_id == id)
            .outerjoin(User, User.id == CalendarEventParticipant.user_id)
            .select_from(CalendarEvent)
            .group_by(CalendarEvent.id)
        )
        result = await self.db.execute(query)
        event = result.mappings().one_or_none()
        return self._build_calendar_event(event) if event else None

    async def list_for_user(self, filters: CalendarEventsListQueryParamsValueObject, order_by: str) -> list[CalendarEventEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "title":
                conditions.append(CalendarEvent.title.ilike(f"%{v}%"))
            elif k == "start":
                conditions.append(CalendarEvent.start >= v)
            elif k == "end":
                conditions.append(CalendarEvent.end <= v)
            elif k == "participants":
                conditions.append(CalendarEventParticipant.user_id.in_(v))
            elif k in ("type", "pending"):
                conditions.append(getattr(CalendarEvent, k) == v)
        query = self._filter_tenant(
            select(
                *CalendarEvent.__table__.columns,
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
            .outerjoin(CalendarEventParticipant, CalendarEventParticipant.event_id == CalendarEvent.id)
            .outerjoin(User, User.id == CalendarEventParticipant.user_id)
            .group_by(CalendarEvent.id)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        events = result.mappings().all()
        return [self._build_calendar_event(event) for event in events]

    async def create(
        self,
        data: CalendarEventCreationValueObject,
    ) -> CalendarEventEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET and k != "participants"}
        query = (
            insert(CalendarEvent)
            .values(
                **kws,
                tenant_id=self._tenant_id,
            )
            .returning(CalendarEvent.id)
        )
        result = await self.db.execute(query)
        event_id = result.scalar_one()
        new_entity = await self.get_by_id(event_id)
        self._audit_create("Calendar_event", event_id, kws)
        return new_entity  # type: ignore

    async def add_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        query = insert(CalendarEventParticipant).values([{"event_id": event_id, "user_id": participant} for participant in participants])
        await self.db.execute(query)

    async def update_participants(self, event_id: UUID, participants: list[UUID]) -> None:
        old_row = await self.db.execute(
            self._filter_tenant(
                select(CalendarEventParticipant.user_id).where(CalendarEventParticipant.event_id == event_id),
            )
        )
        old_participants = old_row.mappings().all()
        query = delete(CalendarEventParticipant).where(CalendarEventParticipant.event_id == event_id)
        await self.db.execute(query)
        query = insert(CalendarEventParticipant).values([{"event_id": event_id, "user_id": participant} for participant in participants])
        await self.db.execute(query)
        self._audit_update(
            "Calendar_event_participant",
            event_id,
            old_values={"participants": old_participants},
            new_values={"participants": participants},
        )

    async def update_data(
        self,
        id: UUID,
        data: CalendarEventUpdateValueObject,
    ) -> CalendarEventEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(CalendarEvent.__table__).where(CalendarEvent.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET and k != "user_id" and k != "participants"}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(CalendarEvent).values(**kws).where(CalendarEvent.id == id))
        await self.db.execute(query)
        new_entity = await self.get_by_id(id)
        self._audit_update("Calendar_event", id, old_values, kws)
        return new_entity  # type: ignore

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(CalendarEvent.__table__).where(CalendarEvent.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(CalendarEvent).where(CalendarEvent.id == id))
        await self.db.execute(query)
        self._audit_delete("Calendar_event", id, old_values)

    async def get_pending_events(self, tenant_id: UUID | None = None) -> list[CalendarEventRemindedEntity]:
        current_date = get_current_datetime().date()
        target_date = current_date + timedelta(days=3)
        query = (
            select(
                CalendarEvent.id,
                CalendarEvent.title,
                CalendarEvent.description,
                CalendarEvent.pending,
                CalendarEvent.tenant_id,
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
            .outerjoin(CalendarEventParticipant, CalendarEventParticipant.event_id == CalendarEvent.id)
            .outerjoin(User, User.id == CalendarEventParticipant.user_id)
            .where(
                CalendarEvent.pending,
                and_(
                    CalendarEvent.start >= current_date,
                    CalendarEvent.end <= target_date,
                ),
            )
            .group_by(CalendarEvent.id)
        )
        if tenant_id is not None:
            query = query.where(CalendarEvent.tenant_id == tenant_id)
        result = await self.db.execute(query)
        events = result.mappings().all()
        return [
            CalendarEventRemindedEntity(
                event_id=event["id"],
                title=event["title"],
                description=event["description"],
                start=event["start"],
                end=event["end"],
                pending=event["pending"],
                participants=[
                    CalendarEventRemindedParticipantEntity(
                        name=participant["name"],
                        email=participant["email"],
                    )
                    for participant in event["participants"]
                ],
            )
            for event in events
        ]

    async def mark_as_notified(self, event_id: UUID) -> None:
        query = self._filter_tenant(update(CalendarEvent).values(pending=False, updated_at=func.now()).where(CalendarEvent.id == event_id))
        await self.db.execute(query)

    def _build_calendar_event(self, data: RowMapping) -> CalendarEventEntity:
        return CalendarEventEntity(
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
                CalendarEventParticipantEntity(
                    id=participant["id"],
                    name=participant["name"],
                )
                for participant in data["participants"]
            ],
        )
