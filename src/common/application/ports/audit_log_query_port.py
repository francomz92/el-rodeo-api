"""Repository port for common-owned audit log export reads."""

from __future__ import annotations

from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IAuditLogQueryRepository(IRepository):
    """Audit-log read access for GDPR export.

    Implementations operate inside the caller's Unit of Work transaction
    boundary and never commit.
    """

    @abstractmethod
    async def fetch_audit_log(self, user_id: UUID) -> list[dict]:
        """Return all-column ``AuditLog`` mappings for the user.

        Newest entries first, limited to the 100 most recent rows.
        """
        raise NotImplementedError
