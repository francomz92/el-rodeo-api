from uuid import UUID

from src.cattle.application.ports.dtos.animal_dtos import AnimalUpdateDTO
from src.cattle.application.ports.repositories.animals_repository_port import IAnimalsRepository
from src.common.application.exceptions import NotPermissionError, ResourceNotFoundError
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
            if not animal.can_delete():
                raise NotPermissionError("No se puede modificar un animal que ya ha sido vendido")
            animal = await repository.update_data(id=id, data=data)
            await uow.commit()
        return animal
