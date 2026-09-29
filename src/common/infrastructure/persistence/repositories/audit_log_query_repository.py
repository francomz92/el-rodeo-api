"""SQLAlchemy implementation of IAuditLogQueryRepository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.application.ports.audit_log_query_port import IAuditLogQueryRepository
from src.common.infrastructure.persistence.models import AuditLog


class AuditLogQueryRepository(IAuditLogQueryRepository):
    """Common-owned audit log reads for GDPR export.

    User-scoped and tenant-agnostic: current GDPR queries filter only by
    ``user_id``. Executes inside the caller's Unit of Work transaction and
    never commits.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def fetch_audit_log(self, user_id: UUID) -> list[dict]:
        rows = await self.db.execute(
            select(AuditLog.__table__).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(100)
        )
        return [dict(row) for row in rows.mappings().all()]
