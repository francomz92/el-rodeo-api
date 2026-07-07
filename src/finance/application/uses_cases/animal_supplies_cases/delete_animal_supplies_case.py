from uuid import UUID

from src.common.application.ports.uow import IUoW
from src.finance.domain.repositories.animal_supplies import IAnimalSuppliesRepository
from src.finance.domain.services.animal_supplies_services.delete_animal_supplies_service import DeleteAnimalSuppliesService


class DeleteAnimalSuppliesCase:
    def __init__(
        self,
        uow: IUoW,
        service: DeleteAnimalSuppliesService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalSuppliesRepository)
            await self.service.validate_delete(id=id, repository=repository)
            await self.service.delete_supply(id=id, repository=repository)
            await uow.commit()
