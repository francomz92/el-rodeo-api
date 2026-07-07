from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import JSONResponse

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.cattle.domain.value_objects.animal_value_object import (
    AnimalCreateValueObject,
    AnimalsListQueryParamsValueObject,
    AnimalUpdateValueObject,
)
from src.cattle.infrastructure.adapters.http.input.animal_schemas import (
    AnimalCreationSchema,
    AnimalsListQueryParamsSchema,
    AnimalUpdateSchema,
)
from src.cattle.infrastructure.adapters.http.output.animal_schemas import AnimalSchema
from src.cattle.infrastructure.presentation.dependencies.animals import (
    GetAnimalDeleteCase,
    GetAnimalListCase,
    GetAnimalRegisterCase,
    GetAnimalUpdateCase,
    GetObtainAnimalCase,
)
from src.common.infrastructure.adapters.http.output.cursor_page import (
    CursorPage,
    encode_cursor,
)

animals_router = APIRouter(
    prefix="/animals",
    responses={401: {}, 403: {}},
    dependencies=[require_role(UserRole.VIEWER)],
)


@animals_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Creates a new animal in the database",
    response_model=AnimalSchema,
    dependencies=[require_role(UserRole.EDITOR)],
)
async def register_animal(
    data: AnimalCreationSchema,
    current_user: GetCurrentUser,
    animal_register_use_case: GetAnimalRegisterCase,
):
    payload = AnimalCreateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
        last_weight=data.initial_weight,
    )
    return await animal_register_use_case.execute(payload)


@animals_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update an animal in the database",
    response_model=AnimalSchema,
    dependencies=[require_role(UserRole.EDITOR)],
)
async def update_animal(
    id: UUID,
    data: AnimalUpdateSchema,
    current_user: GetCurrentUser,
    animal_update_use_case: GetAnimalUpdateCase,
):
    payload = AnimalUpdateValueObject(
        **data.model_dump(exclude_unset=True),
        user_id=current_user.id,
    )
    return await animal_update_use_case.execute(
        id=id,
        data=payload,
    )


@animals_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an animal in the database",
    responses={404: {}, 409: {}},
    dependencies=[require_role(UserRole.ADMIN)],
)
async def delete_animal(
    id: UUID,
    current_user: GetCurrentUser,
    animal_delete_use_case: GetAnimalDeleteCase,
):
    return await animal_delete_use_case.execute(
        id,
    )


@animals_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List all animals by current user authenticated in the database",
    response_model=list[AnimalSchema],
)
async def list_animals_user(
    current_user: GetCurrentUser,
    animal_list_use_case: GetAnimalListCase,
    query_params: Annotated[AnimalsListQueryParamsSchema, Query()],
):
    filters = AnimalsListQueryParamsValueObject(
        **query_params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by", "cursor"},
        ),
    )
    items, total, next_cursor = await animal_list_use_case.execute(
        filters=filters,
        limit=query_params.limit,
        offset=query_params.offset,
        order_by=query_params.order_by,
        cursor=query_params.cursor,
    )

    if query_params.cursor is not None:
        # Return cursor-paginated response (bypasses response_model validation)
        validated = [AnimalSchema.model_validate(a) for a in items]
        page = CursorPage[AnimalSchema](
            items=validated,
            cursor=encode_cursor(str(validated[0].id)) if validated else None,
            next_cursor=next_cursor,
            total=total,
        )
        return JSONResponse(
            content=page.model_dump(mode="json"),
            status_code=status.HTTP_200_OK,
        )

    # Legacy offset/limit response — validated against response_model
    return [AnimalSchema.model_validate(a) for a in items]


@animals_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get an animal in the database",
    response_model=AnimalSchema,
)
async def get_animal(
    id: UUID,
    current_user: GetCurrentUser,
    obtain_animal_case: GetObtainAnimalCase,
):
    return await obtain_animal_case.execute(
        id=id,
    )
