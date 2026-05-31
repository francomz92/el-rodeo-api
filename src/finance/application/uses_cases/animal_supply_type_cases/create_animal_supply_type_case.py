from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.create_animal_supply_type_service import CreateAnimalSupplyTypeService
from src.finance.domain.value_objects.animal_supply_type_value_objects import AnimalSupplyTypeCreateValueObject


class CreateAnimalSupplyTypeCase:
    def __init__(
        self,
        uow: IUoW,
        service: CreateAnimalSupplyTypeService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, data: AnimalSupplyTypeCreateValueObject) -> SupplyTypeEntity:
        async with self.uow as uow:
            repository = uow.get_repository(ISupplyTypesRepository)
            await self.service.validate_duplicated(data, repository)
            supply_type = await self.service.create_new(data, repository)
            await uow.commit()
            return supply_type
