from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity, SupplyTypeEntinty
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objetcts.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
    AnimalSuppliesUpdateValueObject,
)
from src.finance.infrastructure.persistance.models import AnimalSupplie


class AnimalSuppliesRepository(IAnimalSuppliesRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(AnimalSupplie)
            .where(
                AnimalSupplie.id == id,
                AnimalSupplie.user_id == user_id,
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
            select(AnimalSupplie)
            .where(
                AnimalSupplie.id == id,
                AnimalSupplie.user_id == user_id,
            )
            .options(
                joinedload(AnimalSupplie.type),
            )
        )
        result = await self.db.execute(query)
        supplie_db = result.scalar_one_or_none()
        return self._build_animal_supplie_with_type(supplie_db) if supplie_db else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalSupplyEntity]:
        kws = {k: v for k, v in vars(filters).items() if v is not Sentinel.UNSET}
        query = (
            select(AnimalSupplie)
            .where(AnimalSupplie.user_id == user_id)
            .filter_by(**kws)
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .options(
                joinedload(AnimalSupplie.type),
            )
        )
        result = await self.db.execute(query)
        supplies_list = result.scalars().unique().all()
        return [self._build_animal_supplie_with_type(supplie_data) for supplie_data in supplies_list]

    async def create(
        self,
        data: AnimalSuppliesCreateValueObject,
    ) -> AnimalSupplyEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalSupplie).values(**kws).returning(AnimalSupplie.id)
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
            update(AnimalSupplie)
            .where(
                AnimalSupplie.id == id,
                AnimalSupplie.user_id == user_id,
            )
            .values(**kws)
            .returning(AnimalSupplie.id)
        )
        result = await self.db.execute(query)
        updated_id = result.scalar_one()
        return await self.get_by_id(updated_id, data.user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalSupplie).where(AnimalSupplie.id == id)
        await self.db.execute(query)

    def _build_animal_supplie_with_type(
        self,
        supplie_data: AnimalSupplie,
    ) -> AnimalSupplyEntity:
        return AnimalSupplyEntity(
            id=supplie_data.id,
            created_at=supplie_data.created_at,
            name=supplie_data.name,
            amount=supplie_data.amount,
            critical_amount=supplie_data.critical_amount,
            unit_of_measurement=supplie_data.unit_of_measurement,
            description=supplie_data.description,
            type=SupplyTypeEntinty(
                id=supplie_data.type_id,
                name=supplie_data.type.name,
            ),
        )
