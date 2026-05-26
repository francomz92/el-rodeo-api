from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.common.application.ports.uow import IUoW


class DeleteAnimalCase:
    def __init__(self, uow: IUoW, service: DeleteAnimalService) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            await self.service.validate_animal_for_delete(
                id=id,
                user_id=user_id,
                repository=repository,
            )
            await self.service.delete_animal(
                id=id,
                repository=repository,
            )
            await uow.commit()
