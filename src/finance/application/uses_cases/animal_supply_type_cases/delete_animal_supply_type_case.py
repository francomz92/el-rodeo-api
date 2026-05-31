from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.repositories.animal_supply_types import ISupplyTypesRepository
from src.finance.domain.services.animal_supply_type_services.delete_animal_supply_type_service import DeleteAnimalSupplyTypeService


class DeleteAnimalSupplyTypeCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeleteAnimalSupplyTypeService,
    ):
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(ISupplyTypesRepository)
            await self.service.validate_exists(id, repository)
            await self.service.delete(id, repository)
            await uow.commit()
