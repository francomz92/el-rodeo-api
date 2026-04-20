from uuid import UUID

from src.cattle.application.ports.repositories.animals_repository_port import IAnimalsRepository
from src.common.application.exceptions import ResourceNotFoundError
from src.common.application.ports.uow import IUoW


class ObtainAnimalCase:
    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, id: UUID, user_id: UUID):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animal = await repository.get_by_id(id=id, user_id=user_id)
            if not animal:
                raise ResourceNotFoundError("El animal que intenta ver no se encuentra registrado")
            return animal
