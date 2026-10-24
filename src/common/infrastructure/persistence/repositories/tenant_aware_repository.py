from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.common.domain.exceptions import NotPermissionError


class TenantAwareRepository(ABC):
    """Base for all tenant-scoped repositories.

    Provides _filter_tenant() that appends a WHERE tenant_id = X clause
    to any query statement. Tenant scoping is fail-closed: when tenant_id
    is None, _filter_tenant raises NotPermissionError instead of silently
    returning unscoped rows. Use bypass_filter=True only for deliberate
    cross-tenant access (super-admins, system workers iterating every
    tenant).

    Set bypass_filter=True for admin super-users who need cross-tenant access.
    """

    def __init__(
        self,
        session: AsyncSession,
        tenant_id: UUID | None = None,
        bypass_filter: bool = False,
    ) -> None:
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

        Fail-closed: raising (not silently returning unscoped rows) prevents
        a tenant-less token or a worker without context from leaking other
        tenants' data. Cross-tenant access must be granted explicitly via
        bypass_filter.
        """
        if self._bypass:
            return stmt
        if self._tenant_id is None:
            raise NotPermissionError("Falta el contexto de tenant para operar sobre este recurso")
        return stmt.where(self._model.tenant_id == self._tenant_id)  # type: ignore
