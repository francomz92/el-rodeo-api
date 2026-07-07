from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class TenantAwareRepository(ABC):
    """Mandatory base for all tenant-scoped repositories.

    Replaces SessionMixin for tenant repos. Requires tenant_id at construction
    time and provides _filter_tenant() that appends a WHERE tenant_id = X clause
    to any query statement.

    Set bypass_filter=True for admin super-users who need cross-tenant access.
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | None = None,
        bypass_filter: bool = False,
    ) -> None:
        if tenant_id is None and not bypass_filter:
            raise ValueError("tenant_id is required for TenantAwareRepository when bypass_filter is False")
        self.db = session
        self._tenant_id = tenant_id
        self._bypass = bypass_filter

    @property
    @abstractmethod
    def _model(self) -> type:
        """The SQLAlchemy model class to filter by tenant_id."""
        ...

    def _filter_tenant(self, stmt: Any) -> Any:
        """Add WHERE tenant_id = self._tenant_id to the statement.

        When bypass_filter is True, returns the statement unchanged
        (for admin cross-tenant access).
        """
        if self._bypass:
            return stmt
        return stmt.where(self._model.tenant_id == self._tenant_id)  # type: ignore[attr-defined]
