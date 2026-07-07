from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, func, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity, SupplyTypeEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
    AnimalSuppliesUpdateValueObject,
)
from src.finance.infrastructure.persistence.models import AnimalSupply, AnimalSupplyType


class AnimalSuppliesRepository(IAnimalSuppliesRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[AnimalSupply] = AnimalSupply

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(AnimalSupply).where(AnimalSupply.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> AnimalSupplyEntity | None:
        query = self._filter_tenant(
            select(
                *AnimalSupply.__table__.columns,
                AnimalSupplyType.name.label("type_name"),
            )
            .where(AnimalSupply.id == id)
            .outerjoin(
                AnimalSupplyType,
                AnimalSupply.type_id == AnimalSupplyType.id,
            )
        )
        result = await self.db.execute(query)
        supply_db = result.mappings().one_or_none()
        return self._build_animal_supply_with_type(supply_db) if supply_db else None

    async def list_for_user(
        self,
        filters: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalSupplyEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "name":
                conditions.append(AnimalSupply.name.icontains(v))
            elif k in ("id", "type_id"):
                conditions.append(AnimalSupply.id == v)
        query = self._filter_tenant(
            select(
                *AnimalSupply.__table__.columns,
                AnimalSupplyType.name.label("type_name"),
            )
            .where(*conditions)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .outerjoin(
                AnimalSupplyType,
                AnimalSupply.type_id == AnimalSupplyType.id,
            )
        )
        result = await self.db.execute(query)
        supplies_list = result.mappings().all()
        return [self._build_animal_supply_with_type(supply_data) for supply_data in supplies_list]

    async def create(
        self,
        data: AnimalSuppliesCreateValueObject,
    ) -> AnimalSupplyEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["tenant_id"] = self._tenant_id
        query = insert(AnimalSupply).values(**kws).returning(AnimalSupply.id)
        result = await self.db.execute(query)
        suplie_id = result.scalar_one()
        new_entity = await self.get_by_id(suplie_id)
        self._audit_create("animal_supply", suplie_id, kws)
        return new_entity  # type: ignore[return-value]

    async def update_data(
        self,
        id: UUID,
        data: AnimalSuppliesUpdateValueObject,
    ) -> AnimalSupplyEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(AnimalSupply.__table__).where(AnimalSupply.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(AnimalSupply).where(AnimalSupply.id == id).values(**kws).returning(AnimalSupply.id))
        result = await self.db.execute(query)
        updated_id = result.scalar_one()
        new_entity = await self.get_by_id(updated_id)
        self._audit_update("animal_supply", id, old_values, kws)
        return new_entity  # type: ignore[return-value]

    async def increase_stock(self, id: UUID, amount_to_increase: float) -> None:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(AnimalSupply.__table__).where(AnimalSupply.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(
            update(AnimalSupply)
            .where(AnimalSupply.id == id)
            .values(
                amount=AnimalSupply.amount - amount_to_increase,
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update(
            "animal_supply",
            id,
            old_values,
            {"amount": f"decreased_by_{amount_to_increase}"},
        )

    async def delete(self, id: UUID) -> None:
        # Capture old values before delete
        old_row = await self.db.execute(self._filter_tenant(select(AnimalSupply.__table__).where(AnimalSupply.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(AnimalSupply).where(AnimalSupply.id == id))
        await self.db.execute(query)
        self._audit_delete("animal_supply", id, old_values)

    def _build_animal_supply_with_type(self, supply_data: RowMapping) -> AnimalSupplyEntity:
        return AnimalSupplyEntity(
            id=supply_data["id"],
            tenant_id=supply_data["tenant_id"],
            created_at=supply_data["created_at"],
            name=supply_data["name"],
            amount=supply_data["amount"],
            critical_amount=supply_data["critical_amount"],
            unit_of_measurement=supply_data["unit_of_measurement"],
            description=supply_data["description"],
            type=SupplyTypeEntity(
                id=supply_data["type_id"],
                name=supply_data["type_name"],
            ),
        )
