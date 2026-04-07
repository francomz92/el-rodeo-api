from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from src.auth.infrastructure.adapters.http.input.authentication import LoginSchema, RegisterSchema
from src.auth.infrastructure.adapters.http.oputput.authentication import LoginResponseSchema
from src.auth.infrastructure.presentation.dependencies.authentication import GetLoginUserCase, GetRegisterUserCase


auth_router = APIRouter()


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user in the database",
)
async def register_user(
    data: RegisterSchema,
    register_user_case: GetRegisterUserCase,
):
    await register_user_case.execute(dni=data.dni)
    return JSONResponse(content={"message": "User created successfully"})


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate a registered user",
    response_model=LoginResponseSchema,
)
async def login_user(
    data: LoginSchema,
    login_user_case: GetLoginUserCase,
):
    token = await login_user_case.execute(dni=data.dni, password=data.password)
    return LoginResponseSchema(access_token=token)
