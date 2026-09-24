from src.cattle.domain.entities.animal_entity import AnimalEntity
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.value_objects.animal_value_object import AnimalsListQueryParamsValueObject


class ListAnimalService:
    async def get_animals(
        self,
        repository: IAnimalsRepository,
        query: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list[AnimalEntity], int, bool]:
        """List animals matching *query* filters.

        Returns ``(items, total_count, has_next)``.
        When *cursor* is provided, cursor-based pagination is used.
        """
        animals, total, has_next = await repository.list_for_user(
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
            cursor=cursor,
        )
        return animals, total, has_next
