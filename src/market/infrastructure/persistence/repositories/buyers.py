from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, func, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.market.domain.entities.buyers import BuyerEntity
from src.market.domain.repositories.buyers import IBuyersRepository
from src.market.domain.value_objects.buyer_value_objects import (
    BuyerCreateValueObject,
    BuyerListQueryParamsValueObject,
    BuyerUpdateValueObject,
)
from src.market.infrastructure.persistence.models import Buyer


class BuyersRepository(IBuyersRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[Buyer] = Buyer

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(Buyer).where(Buyer.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> BuyerEntity | None:
        query = self._filter_tenant(select(*Buyer.__table__.columns).where(Buyer.id == id))
        result = await self.db.execute(query)
        buyer_db = result.mappings().one_or_none()
        return self._build_buyer(buyer_db) if buyer_db else None

    async def list_for_user(
        self,
        filters: BuyerListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[BuyerEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k in ("name", "contact_number"):
                conditions.append(getattr(Buyer, k).icontains(v))
        query = self._filter_tenant(select(*Buyer.__table__.columns).where(*conditions).limit(limit).offset(offset).order_by(order_by))
        result = await self.db.execute(query)
        buyers_list = result.mappings().all()
        return [self._build_buyer(buyer_data) for buyer_data in buyers_list]

    async def create(self, data: BuyerCreateValueObject) -> BuyerEntity:
        value_dict = {
            "user_id": data.user_id,
            "name": data.name,
            "description": data.description,
            "contact_number": data.contact_number,
            "contact_address": data.contact_address,
            "tenant_id": self._tenant_id,
        }
        query = insert(Buyer).values(**value_dict).returning(Buyer.id)
        result = await self.db.execute(query)
        buyer_id = result.scalar_one()
        new_entity = await self.get_by_id(buyer_id)
        self._audit_create("buyer", buyer_id, value_dict)
        return new_entity  # type: ignore[return-value]

    async def update_data(
        self,
        id: UUID,
        data: BuyerUpdateValueObject,
    ) -> BuyerEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(Buyer.__table__).where(Buyer.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(Buyer).where(Buyer.id == id).values(**kws).returning(Buyer.id))
        result = await self.db.execute(query)
        buyer_id = result.scalar_one()
        new_entity = await self.get_by_id(buyer_id)
        self._audit_update("buyer", id, old_values, kws)
        return new_entity  # type: ignore[return-value]

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(Buyer.__table__).where(Buyer.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(Buyer).where(Buyer.id == id))
        await self.db.execute(query)
        self._audit_delete("buyer", id, old_values)

    def _build_buyer(self, buyer_data: RowMapping) -> BuyerEntity:
        return BuyerEntity(
            id=buyer_data["id"],
            tenant_id=buyer_data["tenant_id"],
            created_at=buyer_data["created_at"],
            name=buyer_data["name"],
            description=buyer_data["description"],
            contact_number=buyer_data["contact_number"],
            contact_address=buyer_data["contact_address"],
        )
