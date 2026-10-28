from uuid import UUID

from src.common.domain.exceptions import NotFoundError
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class GetAnimalSuppliesService:
    async def validate_existence(
        self,
        id: UUID,
        repository: IAnimalSuppliesRepository,
    ) -> AnimalSupplyEntity:
        supply = await repository.get_by_id(id=id)
        if not supply:
            raise NotFoundError("El insumo no existe")
        return supply
