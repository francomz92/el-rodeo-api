from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.value_objects.animal_supplies_value_objects import AnimalSuppliesListQueryParamsValueObject


class ListAnimalSuppliesService:
    async def get_supplies(
        self,
        repository: IAnimalSuppliesRepository,
        query: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ):
        supplies = await repository.list_for_user(
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return supplies
