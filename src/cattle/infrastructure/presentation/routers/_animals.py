from uuid import UUID

from fastapi import APIRouter, status

from src.auth.infrastructure.presentation.dependencies.authentication import GetCurrentUser
from src.cattle.application.ports.dtos.animals import AnimalCreateDTO, AnimalUpdateDTO
from src.cattle.infrastructure.adapters.http.input.animals import AnimalCreationSchema, AnimalUpdateSchema
from src.cattle.infrastructure.adapters.http.output.animals import AnimalSchema
from src.cattle.infrastructure.presentation.dependencies.animals import GetAnimalRegisterCase, GetAnimalUpdateCase


animals_router = APIRouter()


@animals_router.post(
    path="/animals",
    status_code=status.HTTP_201_CREATED,
    summary="Creates a new animal in the database",
    response_model=AnimalSchema,
)
async def register_animal(
    data: AnimalCreationSchema,
    current_user: GetCurrentUser,
    animal_register_use_case: GetAnimalRegisterCase,
):
    payload = AnimalCreateDTO(
        **data.model_dump(),
        user_id=current_user.id,
        last_weight=data.initial_weight,
    )
    return await animal_register_use_case.execute(payload)


@animals_router.put(
    path="/animals/{id}",
    status_code=status.HTTP_200_OK,
    summary="Update an animal in the database",
    response_model=AnimalSchema,
)
async def update_animal(
    id: UUID,
    data: AnimalUpdateSchema,
    current_user: GetCurrentUser,
    animal_update_use_case: GetAnimalUpdateCase,
):
    payload = AnimalUpdateDTO(**data.model_dump(exclude_unset=True), user_id=current_user.id)
    return await animal_update_use_case.execute(id=id, data=payload)
