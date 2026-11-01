from src.cattle.domain.entities.animal_entity import AnimalTypeEntity
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.services.animal_type_services.list_animal_type_params_service import (
    ListAnimalTypeParamsService,
)
from src.common.application.ports.uow import IUoW


class ListAnimalTypeParamsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalTypeParamsService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self) -> list[AnimalTypeEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalTypesRepository)
            return await self.service.get_animal_type_params(
                repository=repository,
            )
