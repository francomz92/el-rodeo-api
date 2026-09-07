from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


class TenantAwareRepository(ABC):
    """Base for all tenant-scoped repositories.

    Provides _filter_tenant() that appends a WHERE tenant_id = X clause
    to any query statement. When tenant_id is None, _filter_tenant is a
    no-op (returns the statement unchanged), allowing usage in contexts
    where tenant scoping is not needed.

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

        When bypass_filter is True, or when tenant_id is None, returns
        the statement unchanged (no tenant scoping).
        """
        if self._bypass or self._tenant_id is None:
            return stmt
        return stmt.where(self._model.tenant_id == self._tenant_id)  # type: ignore
