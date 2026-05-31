from uuid import UUID

from src.cattle.domain.entities.animal_entity import AnimalTypeEntity
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.services.animal_type_services.update_animal_type_service import UpdateAnimalTypeService
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeUpdateValueObject
from src.common.application.ports.uow import IUoW


class UpdateAnimalTypeCase:
    def __init__(self, uow: IUoW, service: UpdateAnimalTypeService) -> None:
        self.uow = uow
        self.service = service

    async def execute(self, id: UUID, data: AnimalTypeUpdateValueObject) -> AnimalTypeEntity:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalTypesRepository)
            await self.service.validate_exists(
                id=id,
                repository=repository,
            )
            await self.service.validate_duplicated(
                name=data.name,
                repository=repository,
            )
            animal = await self.service.update_animal_type(
                id=id,
                data=data,
                repository=repository,
            )
            await uow.commit()
            return animal
