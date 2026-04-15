from fastapi import APIRouter, status
from fastapi.exceptions import ValidationException
from fastapi.responses import JSONResponse

from src.auth.infrastructure.adapters.http.input.authentication import ChangePasswordSchema, LoginSchema, RegisterSchema
from src.auth.infrastructure.adapters.http.oputput.authentication import LoginResponseSchema
from src.auth.infrastructure.presentation.dependencies.authentication import (
    GetChangePasswordCase,
    GetLoginUserCase,
    GetRegisterUserCase,
)
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema


auth_router = APIRouter()


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user in the database",
    response_model=SimpleMessageSchema,
)
async def register_user(data: RegisterSchema, register_user_case: GetRegisterUserCase):
    await register_user_case.execute(dni=data.dni)
    return {"message": "Usuario registrado exitosamente"}


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate a registered user",
    response_model=LoginResponseSchema,
)
async def login_user(data: LoginSchema, login_user_case: GetLoginUserCase):
    token = await login_user_case.execute(dni=data.dni, password=data.password)
    return LoginResponseSchema(access_token=token)


@auth_router.post(
    path="/password-change",
    status_code=status.HTTP_200_OK,
    summary="change a registered user's password",
    response_model=SimpleMessageSchema,
)
async def change_password(
    data: ChangePasswordSchema,
    change_password_case: GetChangePasswordCase,
):
    await change_password_case.execute(
        token=data.token,
        password=data.password,
        new_password=data.new_password,
        confirmed_password=data.confirmed_password,
    )
    return {"message": "Contraseña actualizada exitosamente"}
