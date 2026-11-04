from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.list_animal_supply_type_params_service import (
    ListAnimalSupplyTypeParamsService,
)


class ListAnimalSupplyTypeParamsCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalSupplyTypeParamsService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self) -> list[SupplyTypeEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(ISupplyTypesRepository)
            return await self.service.get_supply_type_params(
                repository=repository,
            )
