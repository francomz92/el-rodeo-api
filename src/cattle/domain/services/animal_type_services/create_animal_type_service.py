from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeCreateValueObject, AnimalTypeListQueryParamsValueObject
from src.common.domain.exceptions import ConflictError


class CreateAnimalTypeService:
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

    async def create_new(
        self,
        data: AnimalTypeCreateValueObject,
        repository: IAnimalTypesRepository,
    ) -> AnimalTypeEntinty:
        return await repository.create(data=data)
