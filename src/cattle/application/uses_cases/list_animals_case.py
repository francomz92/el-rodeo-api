from uuid import UUID

from src.cattle.application.ports.dtos.animal_dtos import AnimalsListQueryParamsDTO
from src.cattle.application.ports.repositories.animals_repository_port import IAnimalsRepository
from src.common.application.ports.uow import IUoW
from src.common.application.types import UNSET


class ListAnimalsCase:
    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        user_id: UUID,
        filters: AnimalsListQueryParamsDTO,
        limit: int,
        offset: int,
        order_by: str,
    ):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animals_list = await repository.list_for_user(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
            )
            return animals_list
