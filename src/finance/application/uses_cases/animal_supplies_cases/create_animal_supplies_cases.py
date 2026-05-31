from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supplies_services.create_animal_supplies_service import CreateAnimalSuppliesService
from src.finance.domain.services.animal_supply_type_services.get_animal_supply_type_service import GetSupplyTypeService
from src.finance.domain.value_objects.animal_supplies_value_objects import AnimalSuppliesCreateValueObject


class CreateAnimalSuppliesCase:
    def __init__(
        self,
        uow: IUoW,
        service: CreateAnimalSuppliesService,
        get_supply_type_service: GetSupplyTypeService,
    ) -> None:
        self.uow = uow
        self.service = service
        self.get_supply_type_service = get_supply_type_service

    async def execute(self, data: AnimalSuppliesCreateValueObject) -> AnimalSupplyEntity:
        self.service.validate_data(data)
        async with self.uow as uow:
            supply_type_repository = uow.get_repository(ISupplyTypesRepository)
            await self.get_supply_type_service.validate_exists(
                id=data.type_id,
                repository=supply_type_repository,
            )
            repository = uow.get_repository(IAnimalSuppliesRepository)
            supply = await self.service.create_new(data, repository)
            await uow.commit()
        return supply
