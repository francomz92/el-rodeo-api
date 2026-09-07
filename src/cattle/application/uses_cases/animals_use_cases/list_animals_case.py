from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.value_objects.animal_value_object import AnimalsListQueryParamsValueObject
from src.common.application.ports.uow import IUoW
from src.common.infrastructure.adapters.http.output.cursor_page import encode_cursor  # TODO: extract cursor encoding to domain port


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
    ) -> tuple[list, int, str | None]:
        """List animals.

        Returns ``(items, total, next_cursor)``.
        When *cursor* is ``None``, *next_cursor* will also be ``None``.
        """
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

        # Compute next_cursor when cursor pagination was used and more items exist
        next_cursor: str | None = None
        if cursor is not None and has_next and items:
            last = items[-1]
            next_cursor = encode_cursor(str(last.id))

        return items, total, next_cursor
