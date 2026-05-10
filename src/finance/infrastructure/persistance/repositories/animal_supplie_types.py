from uuid import UUID

from sqlalchemy import delete, insert, select, update

from src.common.infrastructure.persistence.repositories.mixins import SessionMixin
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository
from src.finance.infrastructure.persistance.models import AnimalSupplieType


class SupplyTypesRepository(ISupplyTypesRepository, SessionMixin):
    async def get_by_id(self, id: UUID) -> SupplyTypeEntinty | None:
        query = select(AnimalSupplieType).where(AnimalSupplieType.id == id)
        result = await self.db.execute(query)
        supply_db = result.scalar_one_or_none()
        return self._build_supply_type(supply_db) if supply_db else None

    async def list_all(self) -> list[SupplyTypeEntinty]:
        query = select(AnimalSupplieType)
        result = await self.db.execute(query)
        supplies_list = result.scalars().all()
        return [self._build_supply_type(supply_data) for supply_data in supplies_list]

    async def create(self, name: str) -> None:
        query = insert(AnimalSupplieType).values(name=name)
        await self.db.execute(query)

    async def update_data(self, id: UUID, name: str) -> None:
        query = (
            update(AnimalSupplieType)
            .where(
                AnimalSupplieType.id == id,
            )
            .values(name=name)
        )
        await self.db.execute(query)

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
