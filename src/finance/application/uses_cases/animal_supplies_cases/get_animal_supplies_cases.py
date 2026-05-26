from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.services.animal_supplies_services.get_animal_supplies_service import GetAnimalSuppliesService


class GetAnimalSuppliesCase:
    def __init__(
        self,
        uow: IUoW,
        service: GetAnimalSuppliesService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalSupplyEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalSuppliesRepository)
            supplies = await self.service.get_animal_supplies(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            return supplies
