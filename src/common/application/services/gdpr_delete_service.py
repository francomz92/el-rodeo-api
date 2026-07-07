"""GDPR Delete Service — anonymizes user data across all bounded contexts.

Performs the GDPR "right to erasure" with data integrity exceptions:
- Business records are anonymized (user_id set to NULL), not deleted
- Account is disabled (is_active = False)
- Refresh tokens are revoked
- Audit log entries are preserved (immutable by law)
"""

from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from src.auth.infrastructure.persistence.models._refresh_token_model import RefreshToken
from src.auth.infrastructure.persistence.models._user_models import User
from src.cattle.infrastructure.persistence.models._animal_models import Animal, AnimalProtocols
from src.cattle.infrastructure.persistence.models._schedule_event_models import ScheduledEvent
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase
from src.market.infrastructure.persistence.models import Buyer, Sale

# Tables that have a user_id column to anonymize
USER_ID_TABLES = [
    Sale.__table__,
    Purchase.__table__,
    Animal.__table__,
    AnimalProtocols.__table__,
    AnimalSupply.__table__,
    ScheduledEvent.__table__,
    Buyer.__table__,
]


class GDPRDeleteService:
    """Application service that anonymizes all user data for GDPR compliance.

    Injected with an AsyncSession to update across bounded contexts.
    Operates within a single transaction.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def delete_user_data(self, user_id: UUID) -> None:
        """Anonymize all data associated with the given user.

        This is NOT a true DELETE — it is anonymization:
        1. Sets user_id = NULL on all business records
        2. Disables the user account (is_active = False)
        3. Revokes all active refresh tokens
        4. Keeps audit log entries (immutable by law)

        Args:
            user_id: The UUID of the user whose data to anonymize.
        """
        conn: AsyncConnection = await self.db.connection()

        if self.db.get_transaction() is None:
            async with conn.begin():
                await self._execute_anonymization(conn, user_id)
        else:
            await self._execute_anonymization(conn, user_id)

    async def _execute_anonymization(
        self,
        conn: AsyncConnection,
        user_id: UUID,
    ) -> None:
        """Execute all anonymization UPDATE statements within a transaction."""
        # 1. Anonymize business records: set user_id = NULL
        for table in USER_ID_TABLES:
            stmt = (
                update(table)  # type: ignore[arg-type]
                .where(table.c.user_id == user_id)
                .values(user_id=None)
            )
            await conn.execute(stmt)

        # 2. Disable user account
        stmt = (
            update(User.__table__)  # type: ignore[arg-type]
            .where(User.__table__.c.id == user_id)
            .values(is_active=False)
        )
        await conn.execute(stmt)

        # 3. Revoke all refresh tokens
        stmt = (
            update(RefreshToken.__table__)  # type: ignore[arg-type]
            .where(RefreshToken.__table__.c.user_id == user_id)
            .where(RefreshToken.__table__.c.revoked_at.is_(None))
            .values(revoked_at=func.now())
        )
        await conn.execute(stmt)

        # 4. Audit log entries are NOT modified (immutable by law)
