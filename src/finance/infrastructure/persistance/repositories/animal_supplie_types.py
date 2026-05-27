from uuid import UUID

from sqlalchemy import and_, delete, exists, insert, select, update

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository
from src.finance.domain.value_objetcts.animal_supply_type_value_objects import (
    AnimalSupplyTypeCreateValueObject,
    AnimalSupplyTypeListQueryParamsValueObject,
    AnimalSupplyTypeUpdateValueObject,
)
from src.finance.infrastructure.persistance.models import AnimalSupplieType


class SupplyTypesRepository(ISupplyTypesRepository, SessionMixin):
    async def exists(self, id: UUID) -> bool:
        query = (
            exists(AnimalSupplieType)
            .where(
                AnimalSupplieType.id == id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(self, id: UUID) -> SupplyTypeEntinty | None:
        query = select(AnimalSupplieType).where(AnimalSupplieType.id == id)
        result = await self.db.execute(query)
        supply_db = result.scalar_one_or_none()
        return self._build_supply_type(supply_db) if supply_db else None

    async def get_by_name(self, name: str) -> SupplyTypeEntinty | None:
        query = select(AnimalSupplieType).where(AnimalSupplieType.name == name)
        result = await self.db.execute(query)
        supply_db = result.scalar_one_or_none()
        return self._build_supply_type(supply_db) if supply_db else None

    async def list(
        self,
        filters: AnimalSupplyTypeListQueryParamsValueObject,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
    ) -> list[SupplyTypeEntinty]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "name":
                conditions.append(AnimalSupplieType.name.icontains(v))
        query = (
            select(AnimalSupplieType)
            .where(
                and_(*conditions),
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        supplies_list = result.scalars().all()
        return [self._build_supply_type(supply_data) for supply_data in supplies_list]

    async def create(self, data: AnimalSupplyTypeCreateValueObject) -> SupplyTypeEntinty:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalSupplieType).values(**kws).returning(AnimalSupplieType.id)
        result = await self.db.execute(query)
        supply_type_id = result.scalar_one()
        return await self.get_by_id(supply_type_id)  # type: ignore

    async def update(self, id: UUID, data: AnimalSupplyTypeUpdateValueObject) -> SupplyTypeEntinty:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(AnimalSupplieType)
            .where(
                AnimalSupplieType.id == id,
            )
            .values(**kws)
        )
        await self.db.execute(query)
        return await self.get_by_id(id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalSupplieType).where(AnimalSupplieType.id == id)
        await self.db.execute(query)

    def _build_supply_type(
        self,
        supply_data: AnimalSupplieType,
    ) -> SupplyTypeEntinty:
        return SupplyTypeEntinty(
            id=supply_data.id,
            name=supply_data.name,
        )
