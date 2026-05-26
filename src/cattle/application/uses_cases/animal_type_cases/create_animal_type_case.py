from src.cattle.domain.entities.animal_entity import AnimalTypeEntinty
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.services.animal_type_services.create_animal_type_service import CreateAnimalTypeService
from src.cattle.domain.value_objects.animal_type_value_object import AnimalTypeCreateValueObject
from src.common.application.ports.uow import IUoW


class CreateAnimalTypeCase:
    def __init__(
        self,
        uow: IUoW,
        service: CreateAnimalTypeService,
    ) -> None:
        self.uow = uow
        self.service = service

    async def execute(
        self,
        data: AnimalTypeCreateValueObject,
    ) -> AnimalTypeEntinty:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalTypesRepository)
            await self.service.validate_duplicated(
                name=data.name,
                repository=repository,
            )
            animal_type = await self.service.create_new(
                data=data,
                repository=repository,
            )
            await uow.commit()
            return animal_type
