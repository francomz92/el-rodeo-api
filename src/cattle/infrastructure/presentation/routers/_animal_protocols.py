from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.auth_dependencies import GetCurrentUser
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolListQueryParamsValueObject,
    AnimalProtocolUpdateValueObject,
)
from src.cattle.infrastructure.adapters.http.input.animal_protocols_schemas import (
    AnimalProtocolsListQueryParamsSchema,
    AnimalProtocolsUpdateSchema,
)
from src.cattle.infrastructure.adapters.http.output.animal_protocols_schemas import AnimalProtocolSchema
from src.cattle.infrastructure.presentation.dependencies.animal_protocols import (
    GetDeleteAnimalProtocolCase,
    GetListAnimalProtocolCase,
    GetObtainAnimalProtocolCase,
    GetUpdateAnimalProtocolsCase,
)

protocols_router = APIRouter(
    prefix="/animal-protocols",
    responses={401: {}, 403: {}},
)


@protocols_router.put(
    path="/{id}",
    response_model=AnimalProtocolSchema,
    summary="Update animal protocol by id",
    responses={404: {}},
)
async def update_animal_protocol(
    id: UUID,
    current_user: GetCurrentUser,
    update_protocol_case: GetUpdateAnimalProtocolsCase,
    data: AnimalProtocolsUpdateSchema,
):
    payload = AnimalProtocolUpdateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await update_protocol_case.execute(id, payload)


@protocols_router.get(
    path="/{id}",
    response_model=AnimalProtocolSchema,
    summary="Get animal protocol by id",
    responses={404: {}},
)
async def get_animal_protocol(
    id: UUID,
    current_user: GetCurrentUser,
    get_protocol_case: GetObtainAnimalProtocolCase,
):
    return await get_protocol_case.execute(id, current_user.id)


@protocols_router.get(
    path="",
    response_model=list[AnimalProtocolSchema],
    summary="List animal protocols for an user",
)
async def list_animal_protocols(
    current_user: GetCurrentUser,
    list_protocol_case: GetListAnimalProtocolCase,
    query_params: AnimalProtocolsListQueryParamsSchema,
):
    filters = AnimalProtocolListQueryParamsValueObject(
        query_params.model_dump(
            exclude={
                "limit",
                "offset",
                "order_by",
            }
        ),
    )
    return await list_protocol_case.execute(
        current_user.id,
        filters,
        query_params.limit,
        query_params.offset,
        query_params.order_by,
    )


@protocols_router.delete(
    path="/{id}",
    summary="Delete animal protocol by id",
    responses={404: {}},
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_animal_protocol(
    id: UUID,
    current_user: GetCurrentUser,
    delete_protocol_case: GetDeleteAnimalProtocolCase,
):
    return await delete_protocol_case.execute(id, current_user.id)
