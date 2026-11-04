from fastapi import APIRouter, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import require_role
from src.cattle.infrastructure.adapters.http.output.animal_type_schemas import AnimalTypeSchema
from src.cattle.infrastructure.presentation.dependencies.animal_type import GetListAnimalTypeParamsCase

animal_type_params_router = APIRouter(
    prefix="/params",
    responses={401: {}, 403: {}},
    # Router-level VIEWER keeps parity with the animal-types list endpoint
    dependencies=[require_role(UserRole.VIEWER)],
)


@animal_type_params_router.get(
    path="/animal-type",
    status_code=status.HTTP_200_OK,
    summary="List animal types as unpaginated reference params",
    response_model=list[AnimalTypeSchema],
)
async def list_animal_type_params(
    use_case: GetListAnimalTypeParamsCase,
):
    return await use_case.execute()
