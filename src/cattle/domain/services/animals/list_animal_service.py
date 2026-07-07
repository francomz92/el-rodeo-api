from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository


class ListAnimalService:
    async def get_animals(
        self,
        repository: IAnimalsRepository,
        query,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list, int, bool]:
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
