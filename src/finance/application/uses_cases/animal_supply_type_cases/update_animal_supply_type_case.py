from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.update_animal_supply_type_service import UpdateAnimalSupplyTypeService
from src.finance.domain.value_objects.animal_supply_type_value_objects import AnimalSupplyTypeUpdateValueObject


class UpdateAnimalSupplyTypeCase:
    def __init__(
        self,
        uow: IUoW,
        service: UpdateAnimalSupplyTypeService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, data: AnimalSupplyTypeUpdateValueObject) -> SupplyTypeEntity:
        async with self.uow as uow:
            repository = uow.get_repository(ISupplyTypesRepository)
            await self.service.validate_exists(id, repository)
            await self.service.validate_duplicated(data, repository)
            supply_type = await self.service.update_supply_type(id, data, repository)
            await uow.commit()
            return supply_type
