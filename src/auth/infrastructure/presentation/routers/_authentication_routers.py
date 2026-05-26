from fastapi import APIRouter, status

from src.auth.domain.value_objects.user_value_object import UserCreationValueObject
from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    ChangePasswordSchema,
    LoginSchema,
    RegisterSchema,
)
from src.auth.infrastructure.adapters.http.oputput.authentication_schemas import LoginResponseSchema
from src.auth.infrastructure.adapters.http.oputput.user_schemas import UserSchema
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetChangePasswordCase,
    GetLoginUserCase,
    GetRegisterUserCase,
    is_admin_user,
)
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema
from src.common.infrastructure.core import settings

auth_router = APIRouter()


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user in the database",
    response_model=UserSchema,
    dependencies=[is_admin_user],
)
async def register_user(
    data: RegisterSchema,
    register_user_case: GetRegisterUserCase,
):
    payload = UserCreationValueObject(**data.model_dump())
    return await register_user_case.execute(
        data=payload,
        redirect_url=f"{settings.DOMAIN}/confirm-account",
    )


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
    token = await login_user_case.execute(
        dni=data.dni,
        password=data.password,
    )
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
    return SimpleMessageSchema(message="Contraseña actualizada exitosamente")
