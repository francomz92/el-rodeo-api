from uuid import UUID

from src.common.domain.exceptions import ConflictError, NotFoundError
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.value_objects.animal_supply_type_value_objects import (
    AnimalSupplyTypeUpdateValueObject,
)


class UpdateAnimalSupplyTypeService:
    async def validate_exists(
        self,
        id: UUID,
        repository: ISupplyTypesRepository,
    ) -> None:
        exists = await repository.get_by_id(id)
        if not exists:
            raise NotFoundError("El tipo de suministro que intenta modificar no existe.")

    async def validate_duplicated(
        self,
        data: AnimalSupplyTypeUpdateValueObject,
        repository: ISupplyTypesRepository,
    ) -> None:
        exists = await repository.get_by_name(data.name)
        if exists:
            raise ConflictError("Ya existe un tipo de suministro con ese nombre.")

    async def update_supply_type(
        self,
        id: UUID,
        data: AnimalSupplyTypeUpdateValueObject,
        repository: ISupplyTypesRepository,
    ) -> SupplyTypeEntity:
        return await repository.update(id, data)
