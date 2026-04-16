from src.cattle.application.ports.dtos.animal_dtos import AnimalCreateDTO, AnimalIdentifierDTO
from src.cattle.application.ports.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.application.ports.repositories.animals_repository_port import IAnimalsRepository
from src.common.application.exceptions import AlreadyExistsError, ValidationError
from src.common.application.ports.uow import IUoW


class RegisterAnimalCase:
    async def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(self, data: AnimalCreateDTO):
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            type_repository = uow.get_repository(IAnimalTypesRepository)
            identifier_data = AnimalIdentifierDTO(
                user_id=data.user_id,
                type_id=data.type_id,
                caravana=data.caravana,
            )
            animal = repository.exists(identifier_data)
            if animal:
                raise AlreadyExistsError("Este animal ya se encuentra registrado")
            type_exists = await type_repository.exists(id=data.type_id)
            if not type_exists:
                raise ValidationError("El tipo de animal seleccionado no es válido")
            animal = await repository.create(data=data)
            await uow.commit()
        return animal
