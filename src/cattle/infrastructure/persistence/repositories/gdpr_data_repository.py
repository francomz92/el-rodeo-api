"""SQLAlchemy implementation of ICattleGDPRDataRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.cattle.domain.repositories.gdpr_data_repository_port import (
    ICattleGDPRDataRepository,
)
from src.cattle.infrastructure.persistence.models import Animal, AnimalProtocols


class CattleGDPRDataRepository(ICattleGDPRDataRepository):
    """Cattle-owned GDPR unlink and export queries.

    User-scoped and tenant-agnostic: current GDPR queries filter only by
    ``user_id``. Executes inside the caller's Unit of Work transaction and
    never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def unlink_user_data(self, user_id: UUID) -> None:
        await self.db.execute(update(Animal).where(Animal.user_id == user_id).values(user_id=None))
        await self.db.execute(update(AnimalProtocols).where(AnimalProtocols.user_id == user_id).values(user_id=None))

    async def fetch_animals(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(Animal.__table__).where(Animal.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]

    async def fetch_animal_protocols(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(AnimalProtocols.__table__).where(AnimalProtocols.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]
