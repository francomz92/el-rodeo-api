from src.common.application.ports.uow import IUoW
from src.finance.domain.entities.animal_supplies import SupplyTypeEntity
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.list_animal_supply_type_service import ListAnimalSupplyTypeService
from src.finance.domain.value_objects.animal_supply_type_value_objects import AnimalSupplyTypeListQueryParamsValueObject


class ListAnimalSupplyTypeCase:
    def __init__(
        self,
        uow: IUoW,
        service: ListAnimalSupplyTypeService,
    ):
        self.uow = uow
        self.service = service

    async def execute(
        self,
        filters: AnimalSupplyTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[SupplyTypeEntity]:
        async with self.uow as uow:
            repository = uow.get_repository(ISupplyTypesRepository)
            return await self.service.get_supply_types(
                filters=filters,
                limit=limit,
                offset=offset,
                order_by=order_by,
                repository=repository,
            )
