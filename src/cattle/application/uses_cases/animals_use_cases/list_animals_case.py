from src.cattle.application.dto import ListAnimalsResult
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.value_objects.animal_value_object import AnimalsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW


class ListAnimalsCase:
    def __init__(self, uow: IUoW, service: ListAnimalService) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> ListAnimalsResult:
        """List animals and return the page data and cursor continuation state."""
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            items, total, has_next = await self.service.get_animals(
                repository=repository,
                query=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                cursor=cursor,
            )

        return ListAnimalsResult(items=items, total=total, has_next=has_next)
