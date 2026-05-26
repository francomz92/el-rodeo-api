from typing import Annotated

from fastapi import Depends

from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork
from src.market.application.uses_cases.buyer_cases.create_buyer_case import CreateBuyerCase
from src.market.application.uses_cases.buyer_cases.delete_buyer_case import DeleteBuyerCase
from src.market.application.uses_cases.buyer_cases.get_buyer_case import GetBuyerCase
from src.market.application.uses_cases.buyer_cases.list_buyer_case import ListBuyerCase
from src.market.application.uses_cases.buyer_cases.update_buyer_case import UpdateBuyerCase
from src.market.domain.services.buyer_services.create_buyer_service import CreateBuyerService
from src.market.domain.services.buyer_services.delete_buyer_service import DeleteBuyerService
from src.market.domain.services.buyer_services.get_buyer_service import GetBuyerService
from src.market.domain.services.buyer_services.list_buyer_service import ListBuyerService
from src.market.domain.services.buyer_services.update_buyer_service import UpdateBuyerService


def _get_create_buyer_case(
    uow: GetUnitOfWork,
    service: Annotated[CreateBuyerService, Depends()],
) -> CreateBuyerCase:
    return CreateBuyerCase(uow, service)


def _get_update_buyer_case(
    uow: GetUnitOfWork,
    service: Annotated[UpdateBuyerService, Depends()],
) -> UpdateBuyerCase:
    return UpdateBuyerCase(uow, service)


def _get_delete_buyer_case(
    uow: GetUnitOfWork,
    service: Annotated[DeleteBuyerService, Depends()],
) -> DeleteBuyerCase:
    return DeleteBuyerCase(uow, service)


def _get_obtain_buyer_case(
    uow: GetUnitOfWork,
    service: Annotated[GetBuyerService, Depends()],
) -> GetBuyerCase:
    return GetBuyerCase(uow, service)


def _get_list_buyers_case(
    uow: GetUnitOfWork,
    service: Annotated[ListBuyerService, Depends()],
) -> ListBuyerCase:
    return ListBuyerCase(uow, service)


GetCreateBuyerCase = Annotated[CreateBuyerCase, Depends(_get_create_buyer_case)]
GetUpdateBuyerCase = Annotated[UpdateBuyerCase, Depends(_get_update_buyer_case)]
GetDeleteBuyerCase = Annotated[DeleteBuyerCase, Depends(_get_delete_buyer_case)]
GetObtainBuyerCase = Annotated[GetBuyerCase, Depends(_get_obtain_buyer_case)]
GetListBuyersCase = Annotated[ListBuyerCase, Depends(_get_list_buyers_case)]
