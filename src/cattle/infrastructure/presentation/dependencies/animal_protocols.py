from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.animal_protocols_cases.delete_animal_protocol_case import DeleteAnimalProtocolCase
from src.cattle.application.uses_cases.animal_protocols_cases.get_animal_protocol_case import GetAnimalProtocolCase
from src.cattle.application.uses_cases.animal_protocols_cases.list_animal_protocols_case import ListAnimalProtocolsCase
from src.cattle.application.uses_cases.animal_protocols_cases.update_animal_protocols_case import UpdateAnimalProtocolsCase
from src.cattle.domain.services.animal_protocols.delete_animal_protocol_service import DeleteAnimalProtocolService
from src.cattle.domain.services.animal_protocols.get_animal_protocol_service import GetAnimalProtocolService
from src.cattle.domain.services.animal_protocols.list_animal_protocol_service import ListAnimalProtocolService
from src.cattle.domain.services.animal_protocols.update_animal_protocol_service import UpdateAnimalProtocolService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_update_animal_protocols_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalProtocolService, Depends()],
) -> UpdateAnimalProtocolsCase:
    return UpdateAnimalProtocolsCase(uow, service)


def _get_obtain_animal_protocol_case(
    uow: GetUnitOfWork,
    service: Annotated[GetAnimalProtocolService, Depends()],
) -> GetAnimalProtocolCase:
    return GetAnimalProtocolCase(uow, service)


def _get_list_animal_protocol_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalProtocolService, Depends()],
) -> ListAnimalProtocolsCase:
    return ListAnimalProtocolsCase(uow, service)


def _get_delete_animal_protocol_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteAnimalProtocolService, Depends()],
) -> DeleteAnimalProtocolCase:
    return DeleteAnimalProtocolCase(uow, service)


GetUpdateAnimalProtocolsCase = Annotated[
    UpdateAnimalProtocolsCase,
    Depends(_get_update_animal_protocols_case),
]

GetObtainAnimalProtocolCase = Annotated[
    GetAnimalProtocolCase,
    Depends(_get_obtain_animal_protocol_case),
]

GetListAnimalProtocolCase = Annotated[
    ListAnimalProtocolsCase,
    Depends(_get_list_animal_protocol_case),
]

GetDeleteAnimalProtocolCase = Annotated[
    DeleteAnimalProtocolCase,
    Depends(_get_delete_animal_protocol_case),
]
