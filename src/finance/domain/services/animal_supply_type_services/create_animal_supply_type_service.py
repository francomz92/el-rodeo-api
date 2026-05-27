from src.common.domain.exceptions import ConflictError
from src.finance.domain.entities.animal_supplies import SupplyTypeEntinty
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository
from src.finance.domain.value_objetcts.animal_supply_type_value_objects import AnimalSupplyTypeCreateValueObject


class CreateAnimalSupplyTypeService:
    async def validate_duplicated(
        self,
        data: AnimalSupplyTypeCreateValueObject,
        repository: ISupplyTypesRepository,
    ):
        existing = await repository.get_by_name(data.name)
        if existing:
            raise ConflictError("Ya existe un tipo de suministro con ese nombre.")

    async def create_new(
        self,
        data: AnimalSupplyTypeCreateValueObject,
        repository: ISupplyTypesRepository,
    ) -> SupplyTypeEntinty:
        return await repository.create(data)
