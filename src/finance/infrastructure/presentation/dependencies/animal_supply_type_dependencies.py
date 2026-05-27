from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.finance.application.uses_cases.animal_supply_type_cases.create_animal_supply_type_case import CreateAnimalSupplyTypeCase
from src.finance.application.uses_cases.animal_supply_type_cases.delete_animal_supply_type_case import DeleteAnimalSupplyTypeCase
from src.finance.application.uses_cases.animal_supply_type_cases.list_animal_supply_type_case import ListAnimalSupplyTypeCase
from src.finance.application.uses_cases.animal_supply_type_cases.update_animal_supply_type_case import UpdateAnimalSupplyTypeCase
from src.finance.domain.services.animal_supply_type_services.create_animal_supply_type_service import CreateAnimalSupplyTypeService
from src.finance.domain.services.animal_supply_type_services.delete_animal_supply_type_service import DeleteAnimalSupplyTypeService
from src.finance.domain.services.animal_supply_type_services.list_animal_supply_type_service import ListAnimalSupplyTypeService
from src.finance.domain.services.animal_supply_type_services.update_animal_supply_type_service import UpdateAnimalSupplyTypeService


def _get_create_animal_supply_type_case(
    uow: GetUnitOfWork,
    service: Annotated[CreateAnimalSupplyTypeService, Depends()],
) -> CreateAnimalSupplyTypeCase:
    return CreateAnimalSupplyTypeCase(uow=uow, service=service)


def _get_update_animal_supply_type_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateAnimalSupplyTypeService, Depends()],
) -> UpdateAnimalSupplyTypeCase:
    return UpdateAnimalSupplyTypeCase(uow=uow, service=service)


def _get_delete_animal_supply_type_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteAnimalSupplyTypeService, Depends()],
) -> DeleteAnimalSupplyTypeCase:
    return DeleteAnimalSupplyTypeCase(uow=uow, service=service)


def _get_list_animal_supply_types_case(
    uow: GetUnitOfWork,
    service: Annotated[ListAnimalSupplyTypeService, Depends()],
) -> ListAnimalSupplyTypeCase:
    return ListAnimalSupplyTypeCase(uow=uow, service=service)


GetCreateAnimalSupplyTypeCase = Annotated[
    CreateAnimalSupplyTypeCase,
    Depends(_get_create_animal_supply_type_case),
]
GetUpdateAnimalSupplyTypeCase = Annotated[
    UpdateAnimalSupplyTypeCase,
    Depends(_get_update_animal_supply_type_case),
]
GetDeleteAnimalSupplyTypeCase = Annotated[
    DeleteAnimalSupplyTypeCase,
    Depends(_get_delete_animal_supply_type_case),
]
GetListAnimalSupplyTypeCase = Annotated[
    ListAnimalSupplyTypeCase,
    Depends(_get_list_animal_supply_types_case),
]
