from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.value_objects.sale_value_objects import (
    SaleCreateValueObject,
    SaleListQueryParamsValueObject,
    SaleUpdateValueObject,
)
from src.market.infrastructure.persistence.models import Sale

from ._mappers import build_sale


class SalesRepository(ISalesRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[Sale] = Sale

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(Sale).where(Sale.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> SaleEntity | None:
        query = self._filter_tenant(select(*Sale.__table__.columns).where(Sale.id == id))
        result = await self.db.execute(query)
        sale_db = result.mappings().one_or_none()
        return build_sale(sale_db) if sale_db else None

    async def list_for_user(
        self,
        filters: SaleListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        user_id: UUID | None = None,  # NOTE: not yet applied as a WHERE filter
    ) -> list[SaleEntity]:
        ALLOWED_ORDER_BY = {"sale_date", "price", "weight", "created_at"}
        if order_by not in ALLOWED_ORDER_BY:
            order_by = "created_at"
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "price":
                conditions.append(Sale.price <= v)
            else:
                conditions.append(getattr(Sale, k) == v)
        query = self._filter_tenant(select(*Sale.__table__.columns).where(*conditions).limit(limit).offset(offset).order_by(order_by))
        result = await self.db.execute(query)
        sales_list_db = result.mappings().all()
        return [build_sale(sale_data) for sale_data in sales_list_db]

    async def create(self, data: SaleCreateValueObject) -> SaleEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["tenant_id"] = self._tenant_id
        query = insert(Sale).values(**kws).returning(Sale.id)
        result = await self.db.execute(query)
        sale_id = result.scalar_one()
        new_entity = await self.get_by_id(sale_id)
        self._audit_create("sale", sale_id, kws)
        return new_entity  # type: ignore

    async def update_data(
        self,
        id: UUID,
        data: SaleUpdateValueObject,
    ) -> SaleEntity | None:
        # Capture old values before update
        old_row = (await self.db.execute(self._filter_tenant(select(Sale.__table__).where(Sale.id == id)))).mappings().one_or_none()
        if old_row is None:
            return None
        old_values = dict(old_row)
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = datetime.now(timezone.utc)
        query = self._filter_tenant(update(Sale).where(Sale.id == id).values(**kws).returning(Sale.id))
        result = await self.db.execute(query)
        sale_id = result.scalar_one()
        new_entity = await self.get_by_id(sale_id)
        self._audit_update("sale", id, old_values, kws)
        return new_entity  # type: ignore

    async def delete(self, id: UUID) -> bool:
        # Capture old values before delete
        old_row = (await self.db.execute(self._filter_tenant(select(Sale.__table__).where(Sale.id == id)))).mappings().one_or_none()
        if old_row is None:
            return False
        old_values = dict(old_row)
        query = self._filter_tenant(delete(Sale).where(Sale.id == id))
        await self.db.execute(query)
        self._audit_delete("sale", id, old_values)
        return True
