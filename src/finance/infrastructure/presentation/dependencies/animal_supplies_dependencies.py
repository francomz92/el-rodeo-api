from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.finance.application.uses_cases.animal_supplies_cases.create_animal_supplies_cases import CreateAnimalSuppliesCase
from src.finance.application.uses_cases.animal_supplies_cases.delete_animal_supplies_case import DeleteAnimalSuppliesCase
from src.finance.application.uses_cases.animal_supplies_cases.get_animal_supplies_cases import GetAnimalSuppliesCase
from src.finance.application.uses_cases.animal_supplies_cases.list_animal_supplies_case import ListAnimalSuppliesCase
from src.finance.application.uses_cases.animal_supplies_cases.update_animal_supplies_case import UpdateAnimalSuppliesCase
from src.finance.domain.services.animal_supplies_services.create_animal_supplies_service import CreateAnimalSuppliesService
from src.finance.domain.services.animal_supplies_services.delete_animal_supplies_service import DeleteAnimalSuppliesService
from src.finance.domain.services.animal_supplies_services.get_animal_supplies_service import GetAnimalSuppliesService
from src.finance.domain.services.animal_supplies_services.list_animal_supplies_service import ListAnimalSuppliesService
from src.finance.domain.services.animal_supplies_services.update_animal_supplies_service import UpdateAnimalSuppliesService
from src.finance.domain.services.animal_supply_type_services.get_animal_supply_type_service import GetSupplyTypeService


def _get_create_animal_supplies_cases(
    uow: GetUnitOfWork,
    service: Annotated[
        CreateAnimalSuppliesService,
        Depends(),
    ],
    get_supply_type_service: Annotated[
        GetSupplyTypeService,
        Depends(),
    ],
) -> CreateAnimalSuppliesCase:
    return CreateAnimalSuppliesCase(uow, service, get_supply_type_service)


def _get_update_animal_supplies_cases(
    uow: GetUnitOfWork,
    service: Annotated[
        UpdateAnimalSuppliesService,
        Depends(),
    ],
    get_supply_type_service: Annotated[
        GetSupplyTypeService,
        Depends(),
    ],
) -> UpdateAnimalSuppliesCase:
    return UpdateAnimalSuppliesCase(uow, service, get_supply_type_service)


def _get_delete_animal_supplies_cases(
    uow: GetUnitOfWork,
    service: Annotated[
        DeleteAnimalSuppliesService,
        Depends(),
    ],
) -> DeleteAnimalSuppliesCase:
    return DeleteAnimalSuppliesCase(uow, service)


def _get_obtain_animal_supplies_cases(
    uow: GetUnitOfWork,
    service: Annotated[
        GetAnimalSuppliesService,
        Depends(),
    ],
) -> GetAnimalSuppliesCase:
    return GetAnimalSuppliesCase(uow, service)


def _get_list_animal_supplies_cases(
    uow: GetUnitOfWork,
    service: Annotated[
        ListAnimalSuppliesService,
        Depends(),
    ],
) -> ListAnimalSuppliesCase:
    return ListAnimalSuppliesCase(uow, service)


GetCreateAnimalSupplyCase = Annotated[
    CreateAnimalSuppliesCase,
    Depends(_get_create_animal_supplies_cases),
]

GetUpdateAnimalSupplyCase = Annotated[
    UpdateAnimalSuppliesCase,
    Depends(_get_update_animal_supplies_cases),
]

GetDeleteAnimalSupplyCase = Annotated[
    DeleteAnimalSuppliesCase,
    Depends(_get_delete_animal_supplies_cases),
]

GetObtainAnimalSupplyCase = Annotated[
    GetAnimalSuppliesCase,
    Depends(_get_obtain_animal_supplies_cases),
]

GetListAnimalSupplyCase = Annotated[
    ListAnimalSuppliesCase,
    Depends(_get_list_animal_supplies_cases),
]
