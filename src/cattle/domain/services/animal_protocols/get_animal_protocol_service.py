from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.common.domain.exceptions import NotFoundError


class GetAnimalProtocolService:
    async def get_animal_protocol(
        self,
        id: UUID,
        user_id: UUID,
        repository: IAnimalProtocolsRepository,
    ) -> AnimalProtocolEntity:
        protocol = await repository.get_by_id(id, user_id)
        if protocol is None:
            raise NotFoundError("No existen protocolos para este animal")
        return protocol
