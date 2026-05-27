from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository
from src.finance.domain.value_objetcts.animal_supply_type_value_objects import AnimalSupplyTypeListQueryParamsValueObject


class ListAnimalSupplyTypeService:
    async def get_supply_types(
        self,
        filters: AnimalSupplyTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        repository: ISupplyTypesRepository,
    ) -> list[SupplyTypeEntinty]:
        return await repository.list(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
