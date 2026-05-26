from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.market.application.uses_cases.sale_cases.create_sale_case import CreateSaleCase
from src.market.application.uses_cases.sale_cases.delete_sale_case import DeleteSaleCase
from src.market.application.uses_cases.sale_cases.get_sale_case import GetSaleCase
from src.market.application.uses_cases.sale_cases.list_sale_case import ListSaleCase
from src.market.domain.services.sale_services.create_sale_service import CreateSaleService
from src.market.domain.services.sale_services.delete_sale_service import DeleteSaleService
from src.market.domain.services.sale_services.get_sale_service import GetSaleService
from src.market.domain.services.sale_services.list_sale_service import ListSaleService


def _get_create_sale_case(
    uow: GetUnitOfWork,
    service: Annotated[CreateSaleService, Depends()],
) -> CreateSaleCase:
    return CreateSaleCase(uow, service)


def _get_delete_sale_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteSaleService, Depends()],
) -> DeleteSaleCase:
    return DeleteSaleCase(uow, service)


def _get_obtain_sale_case(
    uow: GetUnitOfWork,
    service: Annotated[GetSaleService, Depends()],
) -> GetSaleCase:
    return GetSaleCase(uow, service)


def _get_list_sale_case(
    uow: GetUnitOfWork,
    service: Annotated[ListSaleService, Depends()],
) -> ListSaleCase:
    return ListSaleCase(uow, service)


GetCreateSaleCase = Annotated[CreateSaleCase, Depends(_get_create_sale_case)]
GetDeleteSaleCase = Annotated[DeleteSaleCase, Depends(_get_delete_sale_case)]
GetObtainSaleCase = Annotated[GetSaleCase, Depends(_get_obtain_sale_case)]
GetListSaleCase = Annotated[ListSaleCase, Depends(_get_list_sale_case)]
