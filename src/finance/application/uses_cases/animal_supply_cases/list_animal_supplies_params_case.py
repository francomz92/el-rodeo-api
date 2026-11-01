from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.services.animal_supply_services.list_animal_supplies_params_service import (
    ListAnimalSuppliesParamsService,
)


class ListAnimalSuppliesParamsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalSuppliesParamsService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self) -> list[AnimalSupplyEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalSuppliesRepository)
            return await self.service.get_supplies_params(
                repository=repository,
            )
