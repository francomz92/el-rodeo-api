"""SQLAlchemy implementation of IGDPRExportRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.infrastructure.persistence.models import User
from src.cattle.infrastructure.persistence.models import (
    Animal,
    AnimalProtocols,
    ScheduledEvent,
)
from src.common.application.ports.gdpr_export_port import IGDPRExportRepository
from src.common.infrastructure.persistence.models import AuditLog
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase
from src.market.infrastructure.persistence.models import Buyer, Sale


class GDPRExportRepository(IGDPRExportRepository):
    """Queries all user data across bounded contexts for GDPR export."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def fetch_user_profile(self, user_id: UUID) -> dict | None:
        row = await self.db.execute(
            select(
                User.id,
                User.name,
                User.dni,
                User.email,
                User.role,
                User.created_at,
            ).where(User.id == user_id)
        )
        result = row.mappings().one_or_none()
        return dict(result) if result else None

    async def _fetch_all(self, model, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(model.__table__).where(model.user_id == user_id))
        return [dict(r) for r in rows.mappings().all()]

    async def fetch_buyers(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(Buyer, user_id)

    async def fetch_sales(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(Sale, user_id)

    async def fetch_animals(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(Animal, user_id)

    async def fetch_animal_protocols(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(AnimalProtocols, user_id)

    async def fetch_purchases(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(Purchase, user_id)

    async def fetch_animal_supplies(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(AnimalSupply, user_id)

    async def fetch_schedule_events(self, user_id: UUID) -> list[dict]:
        return await self._fetch_all(ScheduledEvent, user_id)

    async def fetch_audit_log(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(
            select(AuditLog.__table__).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(100)
        )
        return [dict(r) for r in rows.mappings().all()]
