from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.common.application.ports.uow import IUoW


class ObtainAnimalCase:
    def __init__(self, uow: IUoW, service: GetAnimalService) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, user_id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            return await self.service.validate_existence_and_get_animal(
                id=id,
                user_id=user_id,
                repository=repository,
            )
