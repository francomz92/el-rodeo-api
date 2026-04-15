from uuid import UUID

from src.cattle.application.ports.dtos.animals import AnimalUpdateDTO
from src.cattle.application.ports.repositories.animals import IAnimalsRepository
from src.common.application.exceptions import ResourceNotFoundError
from src.common.application.ports.uow import IUoW


class UpdateAnimalCase:
    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, id: UUID, data: AnimalUpdateDTO):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animal = await repository.get_by_id(id=id, user_id=data.user_id)
            if not animal:
                raise ResourceNotFoundError("El animal que intenta actualizar no existe")
            await repository.update_data(id=id, data=data)
            await uow.refresh(animal)
        return animal
