from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository


class ListAnimalSupplyTypeParamsService:
    async def get_supply_type_params(
        self,
        repository: ISupplyTypesRepository,
    ) -> list[SupplyTypeEntity]:
        return await repository.list_all()
