from src.cattle.application.ports.dtos.animals import AnimalCreateDTO
from src.cattle.application.ports.repositories.animals import IAnimalsRepository
from src.common.application.exceptions import AlreadyExistsError
from src.common.application.ports.uow import IUoW


class RegisterAnimalCase:
    async def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, data: AnimalCreateDTO):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animal_db = repository.get_by_caravana(caravana=data.caravana)
            if animal_db:
                raise AlreadyExistsError("Este animal ya se encuentra registrado")
            return await repository.create(data=data)
