from uuid import UUID

from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolCreateValueObject


class CreateAnimalProtocolService:
    async def create_new(
        self,
        user_id: UUID,
        data: AnimalProtocolCreateValueObject,
        repository: IAnimalProtocolsRepository,
    ):
        return await repository.create(user_id=user_id, data=data)
