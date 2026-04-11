from datetime import date
from uuid import UUID

from sqlalchemy import delete, select, insert, update
from sqlalchemy.orm import joinedload

from src.cattle.application.ports.repositories.animals import IAnimalsRepository
from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal import AnimalEntity
from src.cattle.infrastructure.persistance.models import Animal
from src.common.infrastructure.persistence.connections.db import AsyncSession


class AnimalRepository(IAnimalsRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID, user_id: UUID | None) -> AnimalEntity | None:
        query = (
            select(Animal)
            .where(Animal.id == id, Animal.user_id == user_id)
            .options(
                joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        animal_db = result.scalar_one_or_none()
        return self._build_animal_with_type(animal_db) if animal_db else None

    async def list_for_user(self, user_id: UUID) -> list[AnimalEntity]:
        query = (
            select(Animal)
            .where(Animal.user_id == user_id)
            .options(
                joinedload(Animal.type),
            )
        )
        result = await self.db.execute(query)
        animal_list_db = result.scalars().unique().all()
        return [self._build_animal_with_type(animal_data) for animal_data in animal_list_db]

    async def create(
        self,
        user_id: UUID,
        animal_type_id: UUID,
        name: str,
        date_of_birth: date,
        initial_weight: float,
        initial_weight_date: date,
        last_weight: float,
        breed: str,
        status: AnimalStatus,
    ) -> None:
        query = insert(Animal).values(
            user_id=user_id,
            type_id=animal_type_id,
            name=name,
            date_of_birth=date_of_birth,
            initial_weight=initial_weight,
            initial_weight_date=initial_weight_date,
            last_weight=last_weight,
            breed=breed,
            status=status,
        )
        await self.db.execute(query)

    async def update_data(
        self,
        id: UUID,
        name: str,
        date_of_birth: date,
        initial_weight: float,
        initial_weight_date: date,
        last_weight: float,
        breed: str,
    ):
        query = (
            update(Animal)
            .where(Animal.id == id)
            .values(
                name=name,
                date_of_birth=date_of_birth,
                initial_weight=initial_weight,
                initial_weight_date=initial_weight_date,
                last_weight=last_weight,
                breed=breed,
            )
        )
        await self.db.execute(query)

    async def update_status(self, id: UUID, status: AnimalStatus):
        query = update(Animal).where(Animal.id == id).values(status=status)
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(Animal).where(Animal.id == id)
        await self.db.execute(query)

    def _build_animal_with_type(self, animal_data: Animal) -> AnimalEntity:
        return AnimalEntity(
            id=animal_data.id,
            name=animal_data.name,
            tag=animal_data.tag,
            date_of_birth=animal_data.date_of_birth,
            initial_weight=animal_data.initial_weight,
            initial_weight_date=animal_data.initial_weight_date,
            last_weight=animal_data.last_weight,
            breed=animal_data.breed,
            status=animal_data.status,
            type=animal_data.type,
        )
