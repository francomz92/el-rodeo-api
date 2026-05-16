from uuid import UUID

from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objetcts.animal_supplies_value_objects import AnimalSuppliesListQueryParamsValueObject


class ListAnimalSuppliesService:
    async def get_animal_supplies(
        self,
        user_id: UUID,
        filters: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: IAnimalSuppliesRepository,
    ) -> list[AnimalSupplyEntity]:
        animal_supplies = await repository.list_for_user(
            user_id=user_id,
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return animal_supplies
