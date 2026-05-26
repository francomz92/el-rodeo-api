from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.market.domain.value_objects.buyer_value_objects import (
    BuyerCreateValueObject,
    BuyerListQueryParamsValueObject,
    BuyerUpdateValueObject,
)
from src.market.infrastructure.adapters.http.input.buyer_schemas import BuyerCreateSchema, BuyerListQueryParamsSchema, BuyerUpdateSchema
from src.market.infrastructure.adapters.http.output.buyer_schemas import BuyerSchema
from src.market.infrastructure.presentation.dependencies.buyer_dependencies import (
    GetCreateBuyerCase,
    GetDeleteBuyerCase,
    GetListBuyersCase,
    GetObtainBuyerCase,
    GetUpdateBuyerCase,
)

buyer_router = APIRouter(
    prefix="/buyers",
    responses={401: {}, 403: {}},
)


@buyer_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new buyer for a user in the database",
    response_model=BuyerSchema,
)
async def create_buyer(
    current_user: GetCurrentUser,
    data: BuyerCreateSchema,
    create_use_case: GetCreateBuyerCase,
):
    payload = BuyerCreateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await create_use_case.execute(data=payload)


@buyer_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update a buyer in the database",
    response_model=BuyerSchema,
)
async def update_buyer(
    id: UUID,
    current_user: GetCurrentUser,
    data: BuyerUpdateSchema,
    update_use_case: GetUpdateBuyerCase,
):
    payload = BuyerUpdateValueObject(**data.model_dump())
    return await update_use_case.execute(
        id=id,
        user_id=current_user.id,
        data=payload,
    )


@buyer_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a buyer from the database",
)
async def delete_buyer(
    id: UUID,
    current_user: GetCurrentUser,
    delete_use_case: GetDeleteBuyerCase,
):
    return await delete_use_case.execute(
        id=id,
        user_id=current_user.id,
    )


@buyer_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get a buyer from the database",
    response_model=BuyerSchema,
)
async def get_buyer(
    id: UUID,
    current_user: GetCurrentUser,
    get_use_case: GetObtainBuyerCase,
):
    return await get_use_case.execute(
        id=id,
        user_id=current_user.id,
    )


@buyer_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List all buyers of a user from the database",
    response_model=BuyerSchema,
)
async def list_buyer(
    current_user: GetCurrentUser,
    filters: BuyerListQueryParamsSchema,
    list_use_case: GetListBuyersCase,
):
    params = BuyerListQueryParamsValueObject(
        **filters.model_dump(
            exclude_unset=True,
            exclude={
                "limit",
                "offset",
                "order_by",
            },
        )
    )
    return await list_use_case.execute(
        user_id=current_user.id,
        filters=params,
        limit=filters.limit,
        offset=filters.offset,
        order_by=filters.order_by,
    )
