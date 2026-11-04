from src.cattle.domain.entities.animal_entity import AnimalTypeEntity
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository


class ListAnimalTypeParamsService:
    async def get_animal_type_params(
        self,
        repository: IAnimalTypesRepository,
    ) -> list[AnimalTypeEntity]:
        return await repository.list_all()
