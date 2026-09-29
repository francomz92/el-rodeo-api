"""SQLAlchemy implementation of IMarketGDPRDataRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.market.domain.repositories.gdpr_data_repository_port import (
    IMarketGDPRDataRepository,
)
from src.market.infrastructure.persistence.models import Buyer, Sale


class MarketGDPRDataRepository(IMarketGDPRDataRepository):
    """Market-owned GDPR unlink and export queries.

    User-scoped and tenant-agnostic: current GDPR queries filter only by
    ``user_id``. Executes inside the caller's Unit of Work transaction and
    never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def unlink_user_data(self, user_id: UUID) -> None:
        await self.db.execute(update(Buyer).where(Buyer.user_id == user_id).values(user_id=None))
        await self.db.execute(update(Sale).where(Sale.user_id == user_id).values(user_id=None))

    async def fetch_buyers(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(Buyer.__table__).where(Buyer.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]

    async def fetch_sales(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(select(Sale.__table__).where(Sale.user_id == user_id))
        return [dict(row) for row in rows.mappings().all()]
