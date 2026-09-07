from uuid import UUID

from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import AnimalProtocolCreateValueObject
from src.common.domain.exceptions import BusinessValidationError


class CreateAnimalProtocolService:
    async def create_new(
        self,
        user_id: UUID,
        data: AnimalProtocolCreateValueObject,
        repository: IAnimalProtocolsRepository,
    ) -> None:
        self._validate_creation(data)
        return await repository.create(user_id=user_id, data=data)

    @staticmethod
    def _validate_creation(data: AnimalProtocolCreateValueObject) -> None:
        if data.vaccinated and not data.vaccinated_date:
            raise BusinessValidationError(
                message="Fecha de vacunación requerida.",
                details=[{"field": "vaccinated_date", "message": "La fecha de vacunación es requerida cuando el animal está vacunado."}],
            )
        if not data.vaccinated and data.vaccinated_date:
            raise BusinessValidationError(
                message="La información de vacunación es inconsistente.",
                details=[
                    {"field": "vaccinated_date", "message": "No puede proporcionar una fecha de vacunación para un animal no vacunado."}
                ],
            )
        if data.sale_permission and not data.sale_permission_date:
            raise BusinessValidationError(
                message="Fecha de permiso de venta requerida.",
                details=[{"field": "sale_permission_date", "message": "Debe ingresar una fecha para el permiso de venta aprobado."}],
            )
        if not data.sale_permission and data.sale_permission_date:
            raise BusinessValidationError(
                message="La información de permiso de venta es inconsistente.",
                details=[
                    {
                        "field": "sale_permission_date",
                        "message": "No puede proporcionar una fecha de permiso de venta para un animal sin permiso.",
                    }
                ],
            )
