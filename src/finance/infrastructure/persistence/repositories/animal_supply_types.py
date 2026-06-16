from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.value_objects.animal_supply_type_value_objects import (
    AnimalSupplyTypeCreateValueObject,
    AnimalSupplyTypeListQueryParamsValueObject,
    AnimalSupplyTypeUpdateValueObject,
)
from src.finance.infrastructure.persistence.models import AnimalSupplyType


class SupplyTypesRepository(ISupplyTypesRepository, SessionMixin):
    async def exists(self, id: UUID) -> bool:
        query = (
            exists(AnimalSupplyType)
            .where(
                AnimalSupplyType.id == id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(self, id: UUID) -> SupplyTypeEntity | None:
        query = select(
            *AnimalSupplyType.__table__.columns,
        ).where(
            AnimalSupplyType.id == id,
        )
        result = await self.db.execute(query)
        supply_db = result.mappings().one_or_none()
        return self._build_supply_type(supply_db) if supply_db else None

    async def get_by_name(self, name: str) -> SupplyTypeEntity | None:
        query = select(
            *AnimalSupplyType.__table__.columns,
        ).where(
            AnimalSupplyType.name == name,
        )
        result = await self.db.execute(query)
        supply_db = result.mappings().one_or_none()
        return self._build_supply_type(supply_db) if supply_db else None

    async def list(
        self,
        filters: AnimalSupplyTypeListQueryParamsValueObject,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> list[SupplyTypeEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "name":
                conditions.append(AnimalSupplyType.name.icontains(v))
        query = (
            select(
                *AnimalSupplyType.__table__.columns,
            )
            .where(
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        supplies_list = result.mappings().all()
        return [self._build_supply_type(supply_data) for supply_data in supplies_list]

    async def create(self, data: AnimalSupplyTypeCreateValueObject) -> SupplyTypeEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalSupplyType).values(**kws).returning(AnimalSupplyType.id)
        result = await self.db.execute(query)
        supply_type_id = result.scalar_one()
        return await self.get_by_id(supply_type_id)  # type: ignore

    async def update(self, id: UUID, data: AnimalSupplyTypeUpdateValueObject) -> SupplyTypeEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(AnimalSupplyType)
            .where(
                AnimalSupplyType.id == id,
            )
            .values(**kws)
        )
        await self.db.execute(query)
        return await self.get_by_id(id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalSupplyType).where(AnimalSupplyType.id == id)
        await self.db.execute(query)

    def _build_supply_type(self, supply_data: RowMapping) -> SupplyTypeEntity:
        return SupplyTypeEntity(
            id=supply_data["id"],
            name=supply_data["name"],
        )
