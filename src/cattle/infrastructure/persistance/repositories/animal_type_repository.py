from uuid import UUID

from sqlalchemy import and_, exists, insert, select, update

from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.value_objects.animal_type_value_object import (
    AnimalTypeCreateValueObject,
    AnimalTypeListQueryParamsValueObject,
    AnimalTypeUpdateValueObject,
)
from src.cattle.infrastructure.persistance.models import AnimalType
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class AnimalTypeRepository(IAnimalTypesRepository, SessionMixin):
    async def exists(self, id: UUID) -> bool:
        query = exists(AnimalType).where(AnimalType.id == id).select()
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(self, id: UUID) -> AnimalTypeEntinty | None:
        query = select(AnimalType).where(AnimalType.id == id)
        result = await self.db.execute(query)
        animal_type_db = result.scalar_one_or_none()
        return self._build_animal_type(animal_type_db) if animal_type_db else None

    async def list(
        self,
        filters: AnimalTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalTypeEntinty]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "id":
                conditions.append(AnimalType.id == v)
            elif k == "name":
                conditions.append(AnimalType.name.icontains(v))
        query = (
            select(AnimalType)
            .where(
                and_(*conditions),
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        animal_types_list = result.scalars().unique().all()
        return [self._build_animal_type(type_data) for type_data in animal_types_list]

    async def create(
        self,
        data: AnimalTypeCreateValueObject,
    ) -> AnimalTypeEntinty:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalType).values(**kws).returning(AnimalType.id)
        result = await self.db.execute(query)
        animal_type_id = result.scalar_one()
        return await self.get_by_id(animal_type_id)  # type: ignore

    async def update(
        self,
        id: UUID,
        data: AnimalTypeUpdateValueObject,
    ) -> AnimalTypeEntinty:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(AnimalType)
            .where(
                AnimalType.id == id,
            )
            .values(**kws)
            .returning(AnimalType.id)
        )
        result = await self.db.execute(query)
        animal_type_id = result.scalar_one_or_none()
        return await self.get_by_id(animal_type_id)  # type: ignore

    def _build_animal_type(self, type_data: AnimalType) -> AnimalTypeEntinty:
        return AnimalTypeEntinty(
            id=type_data.id,
            name=type_data.name,
        )
