from abc import abstractmethod
from uuid import UUID

from src.auth.domain.entities._tenant_entity import TenantEntity
from src.common.domain.repository import IRepository


class ITenantRepository(IRepository):
    @abstractmethod
    async def create(self, name: str, slug: str) -> TenantEntity:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> TenantEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_slug(self, slug: str) -> TenantEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[TenantEntity]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, tenant_id: UUID, plan_id: UUID) -> TenantEntity:
        """Update a tenant's plan_id and return the updated entity."""
        raise NotImplementedError
