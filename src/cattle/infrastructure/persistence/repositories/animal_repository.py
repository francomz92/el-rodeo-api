from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.domain.repositories.animals_repository_port import (
    AnimalCreateValueObject,
    AnimalsListQueryParamsValueObject,
    AnimalUpdateValueObject,
    IAnimalsRepository,
)
from src.cattle.infrastructure.persistence.models import Animal
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class AnimalRepository(IAnimalsRepository, SessionMixin):
    async def exists(
        self,
        id: UUID | None = None,
        user_id: UUID | None = None,
        type_id: UUID | None = None,
        caravana: str | None = None,
    ) -> bool:
        if not id and not all([user_id, type_id, caravana]):
            raise ValueError("Debe proporcionar un id o un conjunto de user_id, type_id y caravana para verificar la existencia")
        if not id:
            query = exists(Animal).where(
                Animal.user_id == user_id,
                Animal.caravana == caravana,
                Animal.type_id == type_id,
            )
        else:
            query = exists(Animal).where(Animal.id == id)
        result = await self.db.execute(query.select())
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalEntity | None:
        query = (
            select(Animal)
            .where(
                Animal.id == id,
                Animal.user_id == user_id,
            )
            .options(
                joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        animal_db = result.scalar_one_or_none()
        return self._build_animal_with_type(animal_db) if animal_db else None

    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        query = (
            select(Animal)
            .where(Animal.caravana == caravana)
            .options(
                joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        animal_db = result.scalar_one_or_none()
        return self._build_animal_with_type(animal_db) if animal_db else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "type_id":
                conditions.append(Animal.type_id == v)
            elif k in ("caravana", "name", "breed"):
                conditions.append(getattr(Animal, k).icontains(v))
        query = (
            select(Animal)
            .where(
                Animal.user_id == user_id,
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
            .options(
                joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        animal_list_db = result.scalars().unique().all()
        return [self._build_animal_with_type(animal_data) for animal_data in animal_list_db]

    async def create(self, data: AnimalCreateValueObject) -> AnimalEntity:
        query = (
            insert(Animal)
            .values(
                **vars(data),
            )
            .returning(Animal.id)
        )
        result = await self.db.execute(query)
        animal_id = result.scalar_one()
        return await self.get_by_id(id=animal_id, user_id=data.user_id)  # type: ignore

    async def update_data(self, id: UUID, data: AnimalUpdateValueObject) -> AnimalEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = update(Animal).where(Animal.id == id).values(**kws)
        await self.db.execute(query)
        return await self.get_by_id(id=id, user_id=data.user_id)  # type: ignore

    async def update_status(self, id: UUID, status: AnimalStatus):
        query = update(Animal).where(Animal.id == id).values(status=status)
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(Animal).where(Animal.id == id)
        await self.db.execute(query)

    def _build_animal_with_type(self, animal_data: Animal) -> AnimalEntity:
        return AnimalEntity(
            id=animal_data.id,
            caravana=animal_data.caravana,
            name=animal_data.name,
            tag=animal_data.tag,
            date_of_birth=animal_data.date_of_birth,
            initial_weight=animal_data.initial_weight,
            initial_weight_date=animal_data.initial_weight_date,
            last_weight=animal_data.last_weight,
            breed=animal_data.breed,
            status=animal_data.status,
            type=AnimalTypeEntity(
                id=animal_data.type.id,
                name=animal_data.type.name,
            ),
        )
