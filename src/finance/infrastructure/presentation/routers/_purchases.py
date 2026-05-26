from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.finance.domain.value_objetcts.purchase_value_objects import (
    PurchaseCreateValueObject,
    PurchaseListQueryParamValueObject,
)
from src.finance.infrastructure.adapters.http.input.purchase_schemas import (
    PurchaseCreateSchema,
    PurchaseListQueryParamsSchema,
)
from src.finance.infrastructure.adapters.http.output.purchase_schemas import PurchaseSchema
from src.finance.infrastructure.presentation.dependencies.purchase_dependencies import (
    GetCreatePurchaseCase,
    GetDeletePurchaseCase,
    GetListPurchaseCase,
    GetObtainPurchaseCase,
)

purchase_router = APIRouter(
    prefix="/purchases",
    responses={401: {}, 403: {}},
)


@purchase_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user purchase in database",
    response_model=PurchaseSchema,
)
async def create_purchase(
    current_user: GetCurrentUser,
    data: PurchaseCreateSchema,
    create_purchase_case: GetCreatePurchaseCase,
):
    payload = PurchaseCreateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await create_purchase_case.execute(payload)


@purchase_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user purchase from database",
)
async def delete_purchase(
    id: UUID,
    current_user: GetCurrentUser,
    delete_purchase_case: GetDeletePurchaseCase,
):
    return await delete_purchase_case.execute(id, current_user.id)


@purchase_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="Get all user purchases from database",
    response_model=list[PurchaseSchema],
)
async def get_purchases(
    current_user: GetCurrentUser,
    filters: PurchaseListQueryParamsSchema,
    list_purchases_case: GetListPurchaseCase,
):
    payload = PurchaseListQueryParamValueObject(
        **filters.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        )
    )
    return await list_purchases_case.execute(
        filter=payload,
        user_id=current_user.id,
        limit=filters.limit,
        offset=filters.offset,
        order_by=filters.order_by,
    )


@purchase_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get a user purchase from database",
    response_model=PurchaseSchema,
)
async def get_purchase(
    id: UUID,
    current_user: GetCurrentUser,
    get_purchase_case: GetObtainPurchaseCase,
):
    return await get_purchase_case.execute(id, current_user.id)
