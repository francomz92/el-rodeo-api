from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.finance.application.uses_cases.purchase_cases.create_purchase_case import CreatePurchaseCase
from src.finance.application.uses_cases.purchase_cases.delete_purchase_case import DeletePurchaseCase
from src.finance.application.uses_cases.purchase_cases.get_purchase_case import GetPurchaseCase
from src.finance.application.uses_cases.purchase_cases.list_purchase_case import ListPurchaseCase
from src.finance.domain.services.purchase_services.create_purchase_service import CreatePurchaseService
from src.finance.domain.services.purchase_services.delete_purchase_service import DeletePurchaseService
from src.finance.domain.services.purchase_services.get_purchase_service import GetPurchaseService
from src.finance.domain.services.purchase_services.list_purchase_service import ListPurchaseService


def _get_create_purchase_case(
    uow: GetUnitOfWork,
    service: Annotated[CreatePurchaseService, Depends()],
) -> CreatePurchaseCase:
    return CreatePurchaseCase(uow, service)


def _get_delete_purchase_case(
    uow: GetUnitOfWork,
    service: Annotated[DeletePurchaseService, Depends()],
) -> DeletePurchaseCase:
    return DeletePurchaseCase(uow, service)


def _get_obtain_purchase_case(
    uow: GetUnitOfWork,
    service: Annotated[GetPurchaseService, Depends()],
) -> GetPurchaseCase:
    return GetPurchaseCase(uow, service)


def _get_list_purchase_case(
    uow: GetUnitOfWork,
    service: Annotated[ListPurchaseService, Depends()],
) -> ListPurchaseCase:
    return ListPurchaseCase(uow, service)


GetCreatePurchaseCase = Annotated[CreatePurchaseCase, Depends(_get_create_purchase_case)]
GetDeletePurchaseCase = Annotated[DeletePurchaseCase, Depends(_get_delete_purchase_case)]
GetObtainPurchaseCase = Annotated[GetPurchaseCase, Depends(_get_obtain_purchase_case)]
GetListPurchaseCase = Annotated[ListPurchaseCase, Depends(_get_list_purchase_case)]
