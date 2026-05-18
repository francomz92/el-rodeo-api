from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.services.animal_supplies_services.list_animal_supplies_service import ListAnimalSuppliesService
from src.finance.domain.value_objetcts.animal_supplies_value_objects import AnimalSuppliesListQueryParamsValueObject


class ListAnimalSuppliesCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalSuppliesService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        user_id: UUID,
        filters: AnimalSuppliesListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalSupplyEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalSuppliesRepository)
            return await self.service.get_animal_supplies(
                user_id=user_id,
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
