from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.animals_use_cases.delete_animal_case import DeleteAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.get_animal_case import ObtainAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.list_animals_case import ListAnimalsCase
from src.cattle.application.uses_cases.animals_use_cases.register_animal_case import RegisterAnimalCase
from src.cattle.application.uses_cases.animals_use_cases.update_animal_case import UpdateAnimalCase
from src.cattle.domain.services.animal_protocols.create_animal_protocol_service import CreateAnimalProtocolService
from src.cattle.domain.services.animals.delete_animal_service import DeleteAnimalService
from src.cattle.domain.services.animals.get_animal_service import GetAnimalService
from src.cattle.domain.services.animals.list_animal_service import ListAnimalService
from src.cattle.domain.services.animals.register_animal_service import RegisterAnimalService
from src.cattle.domain.services.animals.update_animal_service import UpdateAnimalService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_animals_case(
    uow: GetUnitOfWork,
    service: Annotated[RegisterAnimalService, Depends()],
    create_animal_protocol_service: Annotated[
        CreateAnimalProtocolService,
        Depends(),
    ],
):
    return RegisterAnimalCase(
        uow=uow,
        service=service,
        create_animal_protocol_service=create_animal_protocol_service,
    )


def _get_update_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalService, Depends()],
):
    return UpdateAnimalCase(uow, service)


def _get_delete_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteAnimalService, Depends()],
):
    return DeleteAnimalCase(uow=uow, service=service)


def _get_list_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalService, Depends()],
):
    return ListAnimalsCase(uow=uow, service=service)


def _get_obtain_animal_case(
    uow: GetUnitOfWork,
    service: Annotated[GetAnimalService, Depends()],
):
    return ObtainAnimalCase(uow, service)


GetAnimalRegisterCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]
GetAnimalUpdateCase = Annotated[UpdateAnimalCase, Depends(_get_update_animal_case)]
GetAnimalDeleteCase = Annotated[DeleteAnimalCase, Depends(_get_delete_animal_case)]
GetAnimalListCase = Annotated[ListAnimalsCase, Depends(_get_list_animal_case)]
GetObtainAnimalCase = Annotated[ObtainAnimalCase, Depends(_get_obtain_animal_case)]
