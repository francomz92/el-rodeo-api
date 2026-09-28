from uuid import UUID

from sqlalchemy import (
    RowMapping,
    func,
    insert,
    select,
    update as sql_update,
)

from src.auth.domain.entities._tenant_entity import TenantEntity
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.infrastructure.persistence.models import Tenant
from src.common.domain.exceptions import NotFoundError
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class TenantRepository(ITenantRepository, TenantAwareRepository, AuditableRepositoryMixin):
    # Required by TenantAwareRepository ABC; filtering is a no-op at tenant_id=None.
    @property
    def _model(self) -> type:
        return Tenant

    async def create(self, name: str, slug: str) -> TenantEntity:
        stmt = (
            insert(Tenant)
            .values(
                name=name,
                slug=slug,
            )
            .returning(Tenant.id)
        )
        result = await self.db.execute(stmt)
        tenant_id = result.scalar_one()
        new_entity = await self.get_by_id(tenant_id)
        self._audit_create("tenant", tenant_id, {"name": name, "slug": slug})
        return new_entity  # type: ignore

    async def get_by_id(self, id: UUID) -> TenantEntity | None:
        stmt = select(
            Tenant.id,
            Tenant.name,
            Tenant.slug,
            Tenant.plan_id,
            Tenant.created_at,
            Tenant.updated_at,
        ).where(Tenant.id == id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def get_by_slug(self, slug: str) -> TenantEntity | None:
        stmt = select(
            Tenant.id,
            Tenant.name,
            Tenant.slug,
            Tenant.plan_id,
            Tenant.created_at,
            Tenant.updated_at,
        ).where(Tenant.slug == slug)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def list_all(self) -> list[TenantEntity]:
        stmt = select(
            Tenant.id,
            Tenant.name,
            Tenant.slug,
            Tenant.plan_id,
            Tenant.created_at,
            Tenant.updated_at,
        ).order_by(Tenant.created_at)
        result = await self.db.execute(stmt)
        rows = result.mappings().all()
        return [self._build_entity(row) for row in rows]

    @staticmethod
    def _build_entity(row: RowMapping) -> TenantEntity:
        return TenantEntity(
            id=row["id"],
            name=row["name"],
            slug=row["slug"],
            plan_id=row["plan_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update(self, tenant_id: UUID, plan_id: UUID) -> TenantEntity:
        old = await self.get_by_id(tenant_id)
        if not old or not old.plan_id:
            raise NotFoundError(f"Tenant {tenant_id} or plan not found for update")
        old_plan_id = str(old.plan_id) if old.plan_id else None
        stmt = sql_update(Tenant).where(Tenant.id == tenant_id).values(plan_id=plan_id, updated_at=func.now())
        await self.db.execute(stmt)
        result = await self.get_by_id(tenant_id)
        if result is None:
            raise NotFoundError(f"Tenant {tenant_id} not found after update")
        self._audit_update(
            entity_type="tenant",
            entity_id=tenant_id,
            old_values={"plan_id": old_plan_id},
            new_values={"plan_id": str(plan_id)},
        )
        return result
