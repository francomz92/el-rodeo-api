from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import joinedload

from src.common.infrastructure.persistence.connections.db import AsyncSession
from src.finance.application.ports.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.constatns.animal_supplies import UnitOfMeasurement
from src.finance.domain.entities.animal_supplies import AnimalSupplieEntity
from src.finance.infrastructure.persistance.models import AnimalSupplie


class AnimalSuppliesRepository(IAnimalSuppliesRepository):
    def __int__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID, user_id: UUID) -> AnimalSupplieEntity | None:
        query = (
            select(AnimalSupplie)
            .where(AnimalSupplie.id == id, AnimalSupplie.user_id == user_id)
            .options(
                joinedload(AnimalSupplie.type),
            )
        )
        result = await self.db.execute(query)
        supplie_db = result.scalar_one_or_none()
        return self._build_animal_supplie_with_type(supplie_db) if supplie_db else None

    async def list_all(self, user_id: UUID) -> list[AnimalSupplieEntity]:
        query = (
            select(AnimalSupplie)
            .where(AnimalSupplie.user_id == user_id)
            .options(
                joinedload(AnimalSupplie.type),
            )
        )
        result = await self.db.execute(query)
        supplies_list = result.scalars().unique().all()
        return [self._build_animal_supplie_with_type(supplie_data) for supplie_data in supplies_list]

    async def update_data(
        self,
        id: UUID,
        name: str,
        description: str,
        amount: float,
        critical_amount: float,
        unit_of_measurement: UnitOfMeasurement,
    ) -> None:
        query = (
            update(AnimalSupplie)
            .where(AnimalSupplie.id == id)
            .values(
                name=name,
                description=description,
                amount=amount,
                critical_amount=critical_amount,
                unit_of_measurement=unit_of_measurement,
            )
        )
        await self.db.execute(query)

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalSupplie).where(AnimalSupplie.id == id)
        await self.db.execute(query)

    def _build_animal_supplie_with_type(self, supplie_data: AnimalSupplie) -> AnimalSupplieEntity:
        return AnimalSupplieEntity(
            id=supplie_data.id,
            created_at=supplie_data.created_at,
            name=supplie_data.name,
            amount=supplie_data.amount,
            critical_amount=supplie_data.critical_amount,
            unit_of_measurement=supplie_data.unit_of_measurement,
            description=supplie_data.description,
            type=supplie_data.type,
        )
