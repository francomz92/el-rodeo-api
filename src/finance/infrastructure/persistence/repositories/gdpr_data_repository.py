"""SQLAlchemy implementation of IFinanceGDPRDataRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.finance.domain.repositories.gdpr_data_repository_port import (
    IFinanceGDPRDataRepository,
)
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase


class FinanceGDPRDataRepository(IFinanceGDPRDataRepository):
    """Finance-owned GDPR unlink and export queries.

    User-scoped and tenant-agnostic: current GDPR queries filter only by
    ``user_id``. Executes inside the caller's Unit of Work transaction and
    never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def unlink_user_data(self, user_id: UUID) -> None:
        await self.db.execute(update(Purchase).where(Purchase.user_id == user_id).values(user_id=None))
        await self.db.execute(update(AnimalSupply).where(AnimalSupply.user_id == user_id).values(user_id=None))

    async def fetch_purchases(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(Purchase.__table__).where(Purchase.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]

    async def fetch_animal_supplies(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(AnimalSupply.__table__).where(AnimalSupply.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]
