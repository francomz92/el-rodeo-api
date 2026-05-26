from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.finance.domain.value_objetcts.animal_supplies_value_objects import (
    AnimalSuppliesCreateValueObject,
    AnimalSuppliesListQueryParamsValueObject,
    AnimalSuppliesUpdateValueObject,
)
from src.finance.infrastructure.adapters.http.input.animal_supplies_schemas import (
    AnimalSuppliesCreateSchema,
    AnimalSuppliesListQueryParamsSchema,
    AnimalSuppliesUpdateSchema,
)
from src.finance.infrastructure.adapters.http.output.animal_supplies_schemas import AnimalSupplySchema
from src.finance.infrastructure.presentation.dependencies.animal_supplies_dependencies import (
    GetCreateAnimalSupplyCase,
    GetDeleteAnimalSupplyCase,
    GetListAnimalSupplyCase,
    GetObtainAnimalSupplyCase,
    GetUpdateAnimalSupplyCase,
)

animal_supplies_router = APIRouter(
    prefix="/animal-supplies",
    responses={401: {}, 403: {}},
)


@animal_supplies_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    summary="Create an animal supply in data base",
    response_model=AnimalSupplySchema,
)
async def create_animal_supply(
    current_user: GetCurrentUser,
    data: AnimalSuppliesCreateSchema,
    create_animal_supply_case: GetCreateAnimalSupplyCase,
):
    payload = AnimalSuppliesCreateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await create_animal_supply_case.execute(payload)


@animal_supplies_router.put(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update an animal supply in data base",
    response_model=AnimalSupplySchema,
)
async def update_animal_supply(
    current_user: GetCurrentUser,
    id: UUID,
    data: AnimalSuppliesUpdateSchema,
    update_animal_supply_case: GetUpdateAnimalSupplyCase,
):
    payload = AnimalSuppliesUpdateValueObject(
        **data.model_dump(exclude_unset=True),
    )
    return await update_animal_supply_case.execute(
        id=id,
        user_id=current_user.id,
        data=payload,
    )


@animal_supplies_router.delete(
    path="/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an animal supply in data base",
)
async def delete_animal_supply(
    current_user: GetCurrentUser,
    id: UUID,
    delete_animal_supply_case: GetDeleteAnimalSupplyCase,
):
    return await delete_animal_supply_case.execute(
        id=id,
        user_id=current_user.id,
    )


@animal_supplies_router.get(
    path="",
    status_code=status.HTTP_200_OK,
    summary="List all animal supplies of the current user in data base",
    response_model=list[AnimalSupplySchema],
)
async def list_animal_supplies(
    current_user: GetCurrentUser,
    query_params: AnimalSuppliesListQueryParamsSchema,
    list_animal_supplies_case: GetListAnimalSupplyCase,
):
    filters = AnimalSuppliesListQueryParamsValueObject(
        **query_params.model_dump(
            exclude_unset=True,
            exclude={"limit", "offset", "order_by"},
        )
    )
    return await list_animal_supplies_case.execute(
        user_id=current_user.id,
        filters=filters,
        limit=query_params.limit,
        offset=query_params.offset,
        order_by=query_params.order_by,
    )


@animal_supplies_router.get(
    path="/{id}",
    status_code=status.HTTP_200_OK,
    summary="Get an animal supply of the current user by id",
    response_model=AnimalSupplySchema,
)
async def get_animal_supply(
    current_user: GetCurrentUser,
    id: UUID,
    get_animal_supply_case: GetObtainAnimalSupplyCase,
):
    return await get_animal_supply_case.execute(
        id=id,
        user_id=current_user.id,
    )
