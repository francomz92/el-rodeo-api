from uuid import UUID

from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.common.domain.exceptions import ConflictError, NotFoundError


class DeleteAnimalProtocolService:
    async def validate_can_delete(
        self,
        id: UUID,
        user_id: UUID,
        repository: IAnimalProtocolsRepository,
    ) -> None:
        protocol = await repository.get_by_id(id, user_id)
        if protocol is None:
            raise NotFoundError("La información que intenta eliminar no existe.")
        if not protocol.can_delete():
            raise ConflictError("No se pueden eliminar los protocolos de animales vendidos.")

    async def delete_protocol(
        self,
        id: UUID,
        repository: IAnimalProtocolsRepository,
    ) -> None:
        await repository.delete(id)
