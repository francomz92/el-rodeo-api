from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeListQueryParamsValueObject


class ListAnimalTypeService:
    async def get_animal_types(
        self,
        repository: IAnimalTypesRepository,
        filters: AnimalTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalTypeEntinty]:
        return await repository.list(
            filters,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
