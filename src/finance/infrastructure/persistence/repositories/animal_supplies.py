from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity, SupplyTypeEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
    AnimalSuppliesUpdateValueObject,
)
from src.finance.infrastructure.persistence.models import AnimalSupply


class AnimalSuppliesRepository(IAnimalSuppliesRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(AnimalSupply)
            .where(
                AnimalSupply.id == id,
                AnimalSupply.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalSupplyEntity | None:
        query = (
            select(AnimalSupply)
            .where(
                AnimalSupply.id == id,
                AnimalSupply.user_id == user_id,
            )
            .options(
                joinedload(AnimalSupply.type),
            )
        )
        result = await self.db.execute(query)
        supply_db = result.scalar_one_or_none()
        return self._build_animal_supply_with_type(supply_db) if supply_db else None

    async def list_for_user(
        self,
        user_id: UUID,
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
            elif k == ("id", "type_id"):
                conditions.append(AnimalSupply.id == v)
        query = (
            select(AnimalSupply)
            .where(
                AnimalSupply.user_id == user_id,
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .options(
                joinedload(AnimalSupply.type),
            )
        )
        result = await self.db.execute(query)
        supplies_list = result.scalars().unique().all()
        return [self._build_animal_supply_with_type(supply_data) for supply_data in supplies_list]

    async def create(
        self,
        data: AnimalSuppliesCreateValueObject,
    ) -> AnimalSupplyEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalSupply).values(**kws).returning(AnimalSupply.id)
        result = await self.db.execute(query)
        suplie_id = result.scalar_one()
        return await self.get_by_id(suplie_id, data.user_id)  # type: ignore

    async def update_data(
        self,
        id: UUID,
        user_id: UUID,
        data: AnimalSuppliesUpdateValueObject,
    ) -> AnimalSupplyEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(AnimalSupply)
            .where(
                AnimalSupply.id == id,
                AnimalSupply.user_id == user_id,
            )
            .values(**kws)
            .returning(AnimalSupply.id)
        )
        result = await self.db.execute(query)
        updated_id = result.scalar_one()
        return await self.get_by_id(updated_id, data.user_id)  # type: ignore

    async def increase_stock(self, id: UUID, amount_to_increase: float) -> None:
        query = (
            update(AnimalSupply)
            .where(
                AnimalSupply.id == id,
            )
            .values(amount=AnimalSupply.amount - amount_to_increase)
        )
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalSupply).where(AnimalSupply.id == id)
        await self.db.execute(query)

    def _build_animal_supply_with_type(
        self,
        supply_data: AnimalSupply,
    ) -> AnimalSupplyEntity:
        return AnimalSupplyEntity(
            id=supply_data.id,
            created_at=supply_data.created_at,
            name=supply_data.name,
            amount=supply_data.amount,
            critical_amount=supply_data.critical_amount,
            unit_of_measurement=supply_data.unit_of_measurement,
            description=supply_data.description,
            type=SupplyTypeEntity(
                id=supply_data.type_id,
                name=supply_data.type.name,
            ),
        )
