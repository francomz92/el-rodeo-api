from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository


class ListAnimalService:
    async def get_animals(
        self,
        user_id: UUID,
        repository: IAnimalsRepository,
        query,
        limit: int,
        offset: int,
        order_by: str,
    ):
        animals = await repository.list_for_user(
            user_id=user_id,
            filters=query,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )
        return animals
