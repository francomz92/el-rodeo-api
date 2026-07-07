from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class ListAnimalSuppliesService:
    async def get_supplies(
        self,
        repository: IAnimalSuppliesRepository,
        query,
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
