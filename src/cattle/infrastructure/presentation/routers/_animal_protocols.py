from uuid import UUID

from fastapi import APIRouter, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetCurrentUser,
    require_role,
)
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolUpdateValueObject,
)
from src.cattle.infrastructure.adapters.http.input.animal_protocols_schemas import (
    AnimalProtocolsUpdateSchema,
)
from src.cattle.infrastructure.adapters.http.output.animal_protocols_schemas import AnimalProtocolSchema
from src.cattle.infrastructure.presentation.dependencies.animal_protocols import (
    GetDeleteAnimalProtocolCase,
    GetObtainAnimalProtocolCase,
    GetUpdateAnimalProtocolsCase,
)

protocols_router = APIRouter(
    prefix="/animals/{animal_id}/protocols",
    responses={401: {}, 403: {}},
    dependencies=[require_role(UserRole.VIEWER)],
)


@protocols_router.put(
    path="/{id}",
    response_model=AnimalProtocolSchema,
    summary="Update animal protocol by id",
    responses={404: {}},
    dependencies=[require_role(UserRole.EDITOR)],
)
async def update_animal_protocol(
    animal_id: UUID,
    id: UUID,
    current_user: GetCurrentUser,
    update_protocol_case: GetUpdateAnimalProtocolsCase,
    data: AnimalProtocolsUpdateSchema,
):
    payload = AnimalProtocolUpdateValueObject(
        **data.model_dump(),
        user_id=current_user.id,
    )
    return await update_protocol_case.execute(animal_id, id, payload)


@protocols_router.get(
    path="",
    response_model=AnimalProtocolSchema,
    summary="Get animal protocol by id",
    responses={404: {}},
)
async def get_animal_protocol(
    animal_id: UUID,
    current_user: GetCurrentUser,
    get_protocol_case: GetObtainAnimalProtocolCase,
):
    return await get_protocol_case.execute(animal_id)


# @protocols_router.get(
#     path="",
#     response_model=list[AnimalProtocolSchema],
#     summary="List animal protocols for an user",
# )
# async def list_animal_protocols(
#     current_user: GetCurrentUser,
#     list_protocol_case: GetListAnimalProtocolCase,
#     query_params: Annotated[AnimalProtocolsListQueryParamsSchema, Query()],
# ):
#     filters = AnimalProtocolListQueryParamsValueObject(
#         **query_params.model_dump(
#             exclude_unset=True,
#             exclude={
#                 "limit",
#                 "offset",
#                 "order_by",
#             },
#         ),
#     )
#     return await list_protocol_case.execute(
#         filters,
#         query_params.limit,
#         query_params.offset,
#         query_params.order_by,
#     )


@protocols_router.delete(
    path="/{id}",
    summary="Delete animal protocol by id",
    responses={404: {}},
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_role(UserRole.ADMIN)],
)
async def delete_animal_protocol(
    id: UUID,
    current_user: GetCurrentUser,
    delete_protocol_case: GetDeleteAnimalProtocolCase,
):
    return await delete_protocol_case.execute(id)
