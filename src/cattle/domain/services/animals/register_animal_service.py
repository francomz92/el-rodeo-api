from uuid import UUID

from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.common.domain.exceptions import BusinessValidationError, DuplicatedError


class RegisterAnimalService:
    async def validate_duplicate(
        self,
        user_id: UUID,
        type_id: UUID,
        caravana: str,
        repository: IAnimalsRepository,
    ):
        animal_exists = await repository.exists(
            user_id=user_id,
            type_id=type_id,
            caravana=caravana,
        )
        if animal_exists:
            raise DuplicatedError("Este animal ya se encuentra registrado")

    async def validate_type_exists(
        self,
        type_id: UUID,
        repository: IAnimalTypesRepository,
    ) -> None:
        type_exists = await repository.exists(id=type_id)
        if not type_exists:
            raise BusinessValidationError(
                message="Tipo de animal inexistente",
                details=[{"field": "type_id", "message": "Debe seleccionar un tipo válido"}],
            )

    async def create_new(self, data, repository: IAnimalsRepository):
        return await repository.create(data=data)
