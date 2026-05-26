from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.animal_type_cases.create_animal_type_case import CreateAnimalTypeCase
from src.cattle.application.uses_cases.animal_type_cases.list_animal_type_case import ListAnimalTypeCase
from src.cattle.application.uses_cases.animal_type_cases.update_animal_type_case import UpdateAnimalTypeCase
from src.cattle.domain.services.animal_type_services.create_animal_type_service import CreateAnimalTypeService
from src.cattle.domain.services.animal_type_services.list_animal_type_service import ListAnimalTypeService
from src.cattle.domain.services.animal_type_services.update_animal_type_service import UpdateAnimalTypeService
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


async def _get_create_animal_type_case(
    uow: GetUnitOfWork,
    service: Annotated[CreateAnimalTypeService, Depends()],
) -> CreateAnimalTypeCase:
    return CreateAnimalTypeCase(uow=uow, service=service)


async def _get_update_animal_type_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalTypeService, Depends()],
) -> UpdateAnimalTypeCase:
    return UpdateAnimalTypeCase(uow=uow, service=service)


async def get_list_animal_type_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalTypeService, Depends()],
) -> ListAnimalTypeCase:
    return ListAnimalTypeCase(uow=uow, service=service)


GetCreateAnimalTypeCase = Annotated[CreateAnimalTypeCase, Depends(_get_create_animal_type_case)]
GetUpdateAnimalTypeCase = Annotated[UpdateAnimalTypeCase, Depends(_get_update_animal_type_case)]
GetListAnimalTypeCase = Annotated[ListAnimalTypeCase, Depends(get_list_animal_type_case)]
