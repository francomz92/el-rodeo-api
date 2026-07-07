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
from src.auth.infrastructure.persistence.models._tenant_model import Tenant
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class TenantRepository(ITenantRepository, SessionMixin, AuditableRepositoryMixin):
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
        return new_entity  # type: ignore[return-value]

    async def get_by_id(self, id: UUID) -> TenantEntity | None:
        stmt = select(
            Tenant.id,
            Tenant.name,
            Tenant.slug,
            Tenant.plan_id,
            Tenant.created_at,
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
            plan_id=row.get("plan_id"),
            created_at=row["created_at"],
            updated_at=row["created_at"],  # same as created_at until updated
        )

    async def update(self, tenant_id: UUID, plan_id: UUID) -> TenantEntity:
        stmt = sql_update(Tenant).where(Tenant.id == tenant_id).values(plan_id=plan_id, updated_at=func.now())
        await self.db.execute(stmt)
        result = await self.get_by_id(tenant_id)
        assert result is not None, f"Tenant {tenant_id} not found after update"
        return result
