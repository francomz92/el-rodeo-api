from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.market.domain.value_objects.sale_value_objects import (
    SaleCreateValueObject,
    SaleListQueryParamsValueObject,
)
from src.market.infrastructure.adapters.http.input.sale_schemas import (
    SaleCreateSchema,
    SaleListQueryParamsSchema,
)
from src.market.infrastructure.adapters.http.output.sale_schemas import SaleSchema
from src.market.infrastructure.presentation.dependencies.sale_dependencies import (
    GetCreateSaleCase,
    GetDeleteSaleCase,
    GetListSaleCase,
    GetObtainSaleCase,
)

sale_router = APIRouter(
    prefix="/sales",
    responses={401: {}, 403: {}},
)


@sale_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sale in the database",
    response_model=SaleSchema,
)
async def create_sale(
    current_user: GetCurrentUser,
    data: SaleCreateSchema,
    create_use_case: GetCreateSaleCase,
):
    payload = SaleCreateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await create_use_case.execute(data=payload)


@sale_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a sale from the database",
)
async def delete_sale(
    id: UUID,
    current_user: GetCurrentUser,
    delete_use_case: GetDeleteSaleCase,
):
    return await delete_use_case.execute(
        id=id,
        user_id=current_user.id,
    )


@sale_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get a sale from the database",
    response_model=SaleSchema,
)
async def get_sale(
    id: UUID,
    current_user: GetCurrentUser,
    get_use_case: GetObtainSaleCase,
):
    return await get_use_case.execute(
        id=id,
        user_id=current_user.id,
    )


@sale_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List all sales of a user from the database",
    response_model=list[SaleSchema],
)
async def list_sale(
    current_user: GetCurrentUser,
    filters: Annotated[SaleListQueryParamsSchema, Query()],
    list_use_case: GetListSaleCase,
):
    params = SaleListQueryParamsValueObject(
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
