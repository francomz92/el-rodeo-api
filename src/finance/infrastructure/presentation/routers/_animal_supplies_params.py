from fastapi import APIRouter, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import require_role
from src.finance.infrastructure.adapters.http.output.animal_supplies_schemas import (
    AnimalSupplyParamSchema,
)
from src.finance.infrastructure.adapters.http.output.animal_supply_type_schemas import SupplyTypeSchema
from src.finance.infrastructure.presentation.dependencies.animal_supplies_dependencies import (
    GetListAnimalSuppliesParamsCase,
)
from src.finance.infrastructure.presentation.dependencies.animal_supply_type_dependencies import (
    GetListAnimalSupplyTypeParamsCase,
)

supplies_params_router = APIRouter(
    prefix="/params",
    responses={401: {}, 403: {}},
    # Router-level VIEWER keeps parity with the sibling list endpoints
    dependencies=[require_role(UserRole.VIEWER)],
)


@supplies_params_router.get(
    path="/animal-supply",
    status_code=status.HTTP_200_OK,
    summary="List animal supplies as unpaginated reference params",
    response_model=list[AnimalSupplyParamSchema],
)
async def list_animal_supply_params(
    use_case: GetListAnimalSuppliesParamsCase,
):
    return await use_case.execute()


@supplies_params_router.get(
    path="/animal-supply-type",
    status_code=status.HTTP_200_OK,
    summary="List animal supply types as unpaginated reference params",
    response_model=list[SupplyTypeSchema],
)
async def list_animal_supply_type_params(
    use_case: GetListAnimalSupplyTypeParamsCase,
):
    return await use_case.execute()
