from uuid import UUID

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolUpdateValueObject
from src.common.domain.exceptions import ConflictError, NotFoundError


class UpdateAnimalProtocolService:
    async def run_validations(
        self,
        id: UUID,
        data: AnimalProtocolUpdateValueObject,
        repository: IAnimalProtocolsRepository,
    ) -> None:
        protocol = await repository.get_by_id(id, data.user_id)
        if protocol is None:
            raise NotFoundError("El recurso que deseas actualizar no existe")
        if not protocol.can_update():
            raise ConflictError("No se puede actualizar si el animal ya se ha vendido")
        protocol.validate_updated_dates(
            vaccinated=data.vaccinated,
            vaccinated_date=data.vaccinated_date,
            sale_permission=data.sale_permission,
            sale_permission_date=data.sale_permission_date,
        )

    async def update_protocols(
        self,
        id: UUID,
        data,
        repository: IAnimalProtocolsRepository,
    ) -> AnimalProtocolEntity:
        return await repository.update_data(id, data)
