from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    is_admin_user,
    is_authenticated_current_user,
)
from src.cattle.domain.value_objects.animal_type_value_object import (
    AnimalTypeCreateValueObject,
    AnimalTypeListQueryParamsValueObject,
    AnimalTypeUpdateValueObject,
)
from src.cattle.infrastructure.adapters.http.input.animal_type_schemas import (
    AnimalTypeCreateSchema,
    AnimalTypeListQueryParamsSchema,
    AnimalTypeUpdateSchema,
)
from src.cattle.infrastructure.adapters.http.output.animal_type_schemas import AnimalTypeSchema
from src.cattle.infrastructure.presentation.dependencies.animal_type import (
    GetCreateAnimalTypeCase,
    GetListAnimalTypeCase,
    GetUpdateAnimalTypeCase,
)

animal_type_router = APIRouter(
    prefix="/animal-types",
    responses={401: {}, 403: {}},
)


@animal_type_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new animal type in the database, only for administrators",
    response_model=AnimalTypeSchema,
    dependencies=[is_admin_user],
)
async def create_animal_type(
    data: AnimalTypeCreateSchema,
    use_case: GetCreateAnimalTypeCase,
):
    payload = AnimalTypeCreateValueObject(**data.model_dump())
    return await use_case.execute(data=payload)


@animal_type_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    responses={404: {}},
    summary="Update an animal type in the database, only for administrators",
    response_model=AnimalTypeSchema,
    dependencies=[is_admin_user],
)
async def update_animal_type(
    id: UUID,
    data: AnimalTypeUpdateSchema,
    use_case: GetUpdateAnimalTypeCase,
):
    payload = AnimalTypeUpdateValueObject(**data.model_dump())
    return await use_case.execute(id=id, data=payload)


@animal_type_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List animal types in the database",
    response_model=list[AnimalTypeSchema],
    dependencies=[is_authenticated_current_user],
)
async def list_animal_types(
    params: Annotated[AnimalTypeListQueryParamsSchema, Query()],
    use_case: GetListAnimalTypeCase,
):
    filters = AnimalTypeListQueryParamsValueObject(
        **params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        )
    )
    return await use_case.execute(
        filters=filters,
        limit=params.limit,
        offset=params.offset,
        order_by=params.order_by,
    )
