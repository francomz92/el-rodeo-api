from datetime import date
from uuid import UUID

from src.auth.application.services.authentication import AuthService
from src.cattle.application.ports.repositories.animals import IAnimalsRepository
from src.cattle.domain.constants.animal import AnimalStatus
from src.common.application.exceptions import AlreadyExistsError
from src.common.application.ports.uow import IUoW


class RegisterAnimalCase:

    async def __init__(self, uow: IUoW) -> None:
        self.uow = uow


    async def execute(
        self,
        user_id: UUID,
        animal_type_id: UUID,
        caravana: str,
        name: str,
        date_of_birth: date,
        initial_weight: float,
        initial_weight_date: date,
        breed: str,
        tag: str,

    ) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IAnimalsRepository)
            animal_db = repository.get_by_caravana(caravana=caravana)
            if animal_db:
                raise AlreadyExistsError("Este animal ya se encuentra registrado")
            await repository.create(
                user_id=user_id,
                animal_type_id=animal_type_id,
                caravana=caravana,
                name=name,
                date_of_birth=date_of_birth,
                initial_weight=initial_weight,
                initial_weight_date=initial_weight_date,
                last_weight=initial_weight,
                breed=breed,
                tag=tag,
                status=AnimalStatus.NOT_READY,
            )