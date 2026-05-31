from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalTypeEntity
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeListQueryParamsValueObject
from src.common.domain.exceptions import ConflictError, NotFoundError


class UpdateAnimalTypeService:
    async def validate_exists(
        self,
        id: UUID,
        repository: IAnimalTypesRepository,
    ) -> None:
        animal_type_exists = await repository.exists(id)
        if not animal_type_exists:
            raise NotFoundError("El tipo de animal que intenta actualizar no existe.")

    async def validate_duplicated(
        self,
        name: str,
        repository: IAnimalTypesRepository,
    ) -> None:
        animal_type_list = await repository.list(
            filters=AnimalTypeListQueryParamsValueObject(name=name),
            limit=1,
            offset=0,
            order_by="id",
        )
        if animal_type_list:
            raise ConflictError("El tipo de animal que intenta crear ya existe.")

    async def update_animal_type(
        self,
        id: UUID,
        data,
        repository: IAnimalTypesRepository,
    ) -> AnimalTypeEntity:
        return await repository.update(id, data)
