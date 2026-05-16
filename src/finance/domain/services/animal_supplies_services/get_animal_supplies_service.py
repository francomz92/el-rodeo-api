from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class GetAnimalSuppliesService:
    async def get_animal_supplies(
        self,
        id: UUID,
        user_id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> AnimalSupplyEntity:
        animal_supplies = await repository.get_by_id(id, user_id)
        if not animal_supplies:
            raise NotFoundError("Animal supply not found")
        return animal_supplies
