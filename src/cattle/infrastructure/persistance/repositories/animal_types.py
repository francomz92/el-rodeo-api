from uuid import UUID

from sqlalchemy import select

from src.cattle.application.ports.repositories.animal_types import IAnimalTypesRepository
from src.cattle.domain.entities.animal import AnimalTypeEntinty
from src.cattle.infrastructure.persistance.models import AnimalType
from src.common.infrastructure.presentation.dependencies.db import AsyncSession


class AnimalTypeRepository(IAnimalTypesRepository):
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, id: UUID) -> AnimalTypeEntinty | None:
        query = select(AnimalType).where(AnimalType.id == id)
        result = await self.db.execute(query)
        animal_type_db = result.scalar_one_or_none()
        return self._build_animal_type(animal_type_db) if animal_type_db else None

    async def list_all(self) -> list[AnimalTypeEntinty]:
        query = select(AnimalType)
        result = await self.db.execute(query)
        animal_types_list = result.scalars().unique().all()
        return [self._build_animal_type(type_data) for type_data in animal_types_list]

    def _build_animal_type(self, type_data: AnimalType) -> AnimalTypeEntinty:
        return AnimalTypeEntinty(id=type_data.id, name=type_data.name)
