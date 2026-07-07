"""GDPR Export Service — collects all user data across bounded contexts.

This service queries repositories directly using SQLAlchemy Core to collect
every piece of data associated with a user across all contexts: user profile,
buyers, sales, animals, animal protocols, purchases, animal supplies,
schedule events, and audit log entries.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.infrastructure.persistence.models import User
from src.cattle.infrastructure.persistence.models._animal_models import Animal, AnimalProtocols
from src.cattle.infrastructure.persistence.models._schedule_event_models import ScheduledEvent
from src.common.infrastructure.persistence.models._audit_log_model import AuditLog
from src.finance.infrastructure.persistence.models import AnimalSupply, Purchase
from src.market.infrastructure.persistence.models import Buyer, Sale


class GDPRExportService:
    """Application service that collects all user data for GDPR export.

    Injected with an AsyncSession to query across bounded contexts.
    Returns a structured dictionary suitable for JSON serialization.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def export_user_data(self, user_id: UUID) -> dict | None:
        """Collect all data associated with the given user.

        Args:
            user_id: The UUID of the user to export data for.

        Returns:
            A structured dict with sections per context, or None if the user
            does not exist.
        """
        # ── User profile (no password hash!) ──────────────────────────────
        user_row = await self.db.execute(
            select(
                User.id,
                User.name,
                User.dni,
                User.email,
                User.role,
                User.created_at,
            ).where(User.id == user_id)
        )
        user_data = user_row.mappings().one_or_none()
        if user_data is None:
            return None

        # ── Buyers ────────────────────────────────────────────────────────
        buyers = await self._fetch_all(Buyer, user_id)

        # ── Sales ─────────────────────────────────────────────────────────
        sales = await self._fetch_all(Sale, user_id)

        # ── Animals ───────────────────────────────────────────────────────
        animals = await self._fetch_all(Animal, user_id)

        # ── Animal protocols ──────────────────────────────────────────────
        protocols = await self._fetch_all(AnimalProtocols, user_id)

        # ── Purchases ─────────────────────────────────────────────────────
        purchases = await self._fetch_all(Purchase, user_id)

        # ── Animal supplies ───────────────────────────────────────────────
        supplies = await self._fetch_all(AnimalSupply, user_id)

        # ── Schedule events ───────────────────────────────────────────────
        events = await self._fetch_all(ScheduledEvent, user_id)

        # ── Audit log (recent entries) ────────────────────────────────────
        audit_rows = await self.db.execute(
            select(AuditLog.__table__).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(100)
        )
        audit_log = [dict(row) for row in audit_rows.mappings().all()]

        return {
            "user_profile": dict(user_data),
            "buyers": buyers,
            "sales": sales,
            "animals": animals,
            "animal_protocols": protocols,
            "purchases": purchases,
            "animal_supplies": supplies,
            "schedule_events": events,
            "audit_log": audit_log,
        }

    async def _fetch_all(self, model, user_id: UUID) -> list[dict]:
        """Fetch all rows from a given table WHERE user_id matches."""
        rows = await self.db.execute(
            select(model.__table__).where(model.user_id == user_id)  # type: ignore[attr-defined]
        )
        return [dict(row) for row in rows.mappings().all()]
