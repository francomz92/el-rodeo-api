from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import AnimalSupplyEntity
from src.finance.domain.repositories.animal_supplie_types import ISupplyTypesRepository
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.services.animal_supplies_services.update_animal_supplies_service import UpdateAnimalSuppliesService
from src.finance.domain.services.animal_supply_type_services.get_animal_supply_type_service import GetSupplyTypeService
from src.finance.domain.value_objetcts.animal_supplies_value_objects import AnimalSuppliesUpdateValueObject


class UpdateAnimalSuppliesCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateAnimalSuppliesService,
        get_supply_type_service: GetSupplyTypeService,
    ) -> None:
        self.uow = uow
        self.service = service
        self.get_supply_type_service = get_supply_type_service

    async def execute(
        self,
        id: UUID,
        user_id: UUID,
        data: AnimalSuppliesUpdateValueObject,
    ) -> AnimalSupplyEntity:
        self.service.validate_data(data)
        async with self.uow as uow:
            supply_type_repository = uow.get_repository(ISupplyTypesRepository)
            await self.get_supply_type_service.validate_exists(
                id=data.type_id,
                repository=supply_type_repository,
            )
            repository = uow.get_repository(IAnimalSuppliesRepository)
            animal_supply = await self.service.update_animal_supplies(
                id=id,
                user_id=user_id,
                data=data,
                repository=repository,
            )
            await uow.commit()
        return animal_supply
