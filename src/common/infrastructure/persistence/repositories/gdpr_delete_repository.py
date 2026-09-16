"""SQLAlchemy implementation of IGDPRDeleteRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.infrastructure.persistence.models import (
    RefreshToken,
    User,
)
from src.calendar.infrastructure.persistence.models import CalendarEvent
from src.cattle.infrastructure.persistence.models import (
    Animal,
    AnimalProtocols,
)
from src.common.application.ports.gdpr_delete_port import IGDPRDeleteRepository
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase
from src.market.infrastructure.persistence.models import Buyer, Sale

USER_ID_TABLES = [
    Sale.__table__,
    Purchase.__table__,
    Animal.__table__,
    AnimalProtocols.__table__,
    AnimalSupply.__table__,
    CalendarEvent.__table__,
    Buyer.__table__,
]


class GDPRDeleteRepository(IGDPRDeleteRepository):
    """Anonymizes user data across bounded contexts for GDPR compliance.

    Operates within the Unit of Work transaction boundary. The caller
    (use case) is responsible for committing the Unit of Work.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def delete_user_data(self, user_id: UUID) -> None:
        """Set user_id = NULL on all business records, disable account,
        and revoke refresh tokens."""
        for table in USER_ID_TABLES:
            stmt = (
                update(table)  # type: ignore
                .where(table.c.user_id == user_id)
                .values(user_id=None)
            )
            await self.db.execute(stmt)

        stmt = (
            update(User.__table__)  # type: ignore
            .where(User.__table__.c.id == user_id)
            .values(is_active=False)
        )
        await self.db.execute(stmt)

        stmt = (
            update(RefreshToken.__table__)  # type: ignore
            .where(RefreshToken.__table__.c.user_id == user_id)
            .where(RefreshToken.__table__.c.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
        await self.db.execute(stmt)
