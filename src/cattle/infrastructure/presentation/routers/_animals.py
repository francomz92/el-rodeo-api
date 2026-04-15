from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.auth.infrastructure.presentation.dependencies.authentication import GetAuthService, GetCurrentUser
from src.cattle.infrastructure.adapters.http.input.animals import AnimalCreationSchema
from src.cattle.infrastructure.adapters.http.output.animals import AnimalSchema
from src.cattle.infrastructure.presentation.dependencies.animals import GetAnimalsCase
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema



animals_router = APIRouter()



@animals_router.post(
    path="/animals",
    status_code=status.HTTP_201_CREATED,
    summary="Creates a new animal in the database",
    response_model=SimpleMessageSchema,
)
async def register_animal(
    data: AnimalCreationSchema,
    current_user: GetCurrentUser,
    animal_use_case: GetAnimalsCase,
):
    await animal_use_case.execute(
        user_id=current_user.id,
        animal_type_id=data.animal_type_id,
        caravana=data.caravana,
        name=data.name,
        date_of_birth=data.date_of_birth,
        initial_weight=data.initial_weight,
        initial_weight_date=data.initial_weight_date,
        breed=data.breed,
        tag=data.tag,
    )
    return {"message": f"Caravana {data.caravana} registrado exitosamente"}