from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.services.animal_type_services.list_animal_type_service import ListAnimalTypeService
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeListQueryParamsValueObject
from src.common.application.ports.uow import IUoW


class ListAnimalTypeCase:
    def __init__(self, uow: IUoW, service: ListAnimalTypeService) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        filters: AnimalTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalTypeEntinty]:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalTypesRepository)
            return await self.service.get_animal_types(
                repository=repository,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )
