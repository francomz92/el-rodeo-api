from uuid import UUID

from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.cattle.domain.value_objects.animal_value_objenct import AnimalUpdateValueObject
from src.common.application.ports.uow import IUoW


class UpdateAnimalCase:
    def __init__(self, uow: IUoW, service: UpdateAnimalService) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, data: AnimalUpdateValueObject):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            await self.service.validate_existence(
                id=id,
                user_id=data.user_id,
                repository=repository,
            )
            animal = await self.service.update_animal(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()
        return animal
