from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository


class ListAnimalSuppliesParamsService:
    async def get_supplies_params(
        self,
        repository: IAnimalSuppliesRepository,
    ) -> list[AnimalSupplyEntity]:
        return await repository.list_all_for_user()
