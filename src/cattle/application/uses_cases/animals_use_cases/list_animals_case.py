from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.value_objects.animal_value_objenct import AnimalsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW


class ListAnimalsCase:
    def __init__(self, uow: IUoW, service: ListAnimalService) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            return await self.service.get_animals(
                user_id=user_id,
                repository=repository,
                query=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )
