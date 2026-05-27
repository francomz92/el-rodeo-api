from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import is_admin_user
from src.finance.domain.value_objetcts.animal_supply_type_value_objects import (
    AnimalSupplyTypeCreateValueObject,
    AnimalSupplyTypeListQueryParamsValueObject,
    AnimalSupplyTypeUpdateValueObject,
)
from src.finance.infrastructure.adapters.http.input.animal_supply_type_schemas import (
    AnimalSupplyTypeCreateSchema,
    AnimalSupplyTypeListQueryParamsSchema,
    AnimalSupplyTypeUpdateSchema,
)
from src.finance.infrastructure.adapters.http.output.animal_suply_type_schemas import SupplyTypeSchema
from src.finance.infrastructure.presentation.dependencies.animal_supply_type_dependencies import (
    GetCreateAnimalSupplyTypeCase,
    GetDeleteAnimalSupplyTypeCase,
    GetListAnimalSupplyTypeCase,
    GetUpdateAnimalSupplyTypeCase,
)

supply_type_router = APIRouter(
    prefix="/supply-types",
    responses={401: {}, 403: {}},
)


@supply_type_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new supply type in the database",
    response_model=SupplyTypeSchema,
    dependencies=[is_admin_user],
)
async def create_supply_type(
    data: AnimalSupplyTypeCreateSchema,
    use_case: GetCreateAnimalSupplyTypeCase,
):
    payload = AnimalSupplyTypeCreateValueObject(
        **data.model_dump(),
    )
    return await use_case.execute(data=payload)


@supply_type_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update a supply type in the database",
    response_model=SupplyTypeSchema,
    dependencies=[is_admin_user],
)
async def update_supply_type(
    id: UUID,
    data: AnimalSupplyTypeUpdateSchema,
    use_case: GetUpdateAnimalSupplyTypeCase,
):
    payload = AnimalSupplyTypeUpdateValueObject(
        **data.model_dump(),
    )
    return await use_case.execute(id=id, data=payload)


@supply_type_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a supply type from the database",
    dependencies=[is_admin_user],
)
async def delete_supply_type(
    id: UUID,
    use_case: GetDeleteAnimalSupplyTypeCase,
):
    return await use_case.execute(id=id)


@supply_type_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List supply types from the database",
    response_model=list[SupplyTypeSchema],
    dependencies=[is_admin_user],
)
async def get_supply_types(
    query_params: Annotated[AnimalSupplyTypeListQueryParamsSchema, Query()],
    use_case: GetListAnimalSupplyTypeCase,
):
    filters = AnimalSupplyTypeListQueryParamsValueObject(
        **query_params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        )
    )
    return await use_case.execute(
        filters=filters,
        limit=query_params.limit,
        offset=query_params.offset,
        order_by=query_params.order_by,
    )
