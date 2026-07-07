from fastapi import APIRouter, Request, Response, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.value_objects.user_value_object import UserCreationValueObject
from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    ChangePasswordSchema,
    LoginSchema,
    RegisterSchema,
)
from src.auth.infrastructure.adapters.http.input.user_schemas import (
    UpdateProfileSchema,
)
from src.auth.infrastructure.adapters.http.output.authentication_schemas import (
    LoginResponseSchema,
)
from src.auth.infrastructure.adapters.http.output.user_schemas import UserSchema
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetChangePasswordCase,
    GetCurrentUser,
    GetLoginUserCase,
    GetLogoutUserCase,
    GetOauthToken,
    GetRegisterUserCase,
    require_role,
)
from src.auth.infrastructure.presentation.dependencies.user_dependencies import (
    GetUpdateUserProfileCaseDep,
    GetUserProfileCaseDep,
)
from src.common.domain.exceptions import UnauthorizedError
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema
from src.common.infrastructure.adapters.security.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

auth_router = APIRouter()


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user in the database",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.ADMIN)],
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
    description="Returns access and refresh tokens. Sets HttpOnly cookies when X-Requested-With: XMLHttpRequest is present (web clients).",
    response_model=LoginResponseSchema,
)
@rate_limit("5/minute")
async def login_user(
    data: LoginSchema,
    login_user_case: GetLoginUserCase,
    request: Request,
    response: Response,
):
    access_token, refresh_token = await login_user_case.execute(
        dni=data.dni,
        password=data.password,
    )

    # Set HttpOnly cookies for web clients (X-Requested-With: XMLHttpRequest)
    requested_with = request.headers.get("x-requested-with", "")
    if requested_with == "XMLHttpRequest":
        set_auth_cookies(response, access_token, refresh_token, settings)

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.post(
    path="/password-change",
    status_code=status.HTTP_200_OK,
    summary="Change a registered user's password",
    description="Requires authentication via Bearer token. Revokes all refresh tokens on success (forces re-login).",
    response_model=SimpleMessageSchema,
)
@rate_limit("3/minute")
async def change_password(
    data: ChangePasswordSchema,
    change_password_case: GetChangePasswordCase,
    current_user: GetCurrentUser,
    request: Request,
):
    await change_password_case.execute(
        user=current_user,
        password=data.password,
        new_password=data.new_password,
        confirmed_password=data.confirmed_password,
    )
    return SimpleMessageSchema(message="Contraseña actualizada exitosamente")


@auth_router.post(
    path="/logout",
    status_code=status.HTTP_200_OK,
    summary="Invalidate the current token (logout)",
    description="Blacklists the access token, clears auth cookies, and revokes all refresh tokens for the user.",
    response_model=SimpleMessageSchema,
)
async def logout_user(
    token: GetOauthToken,
    logout_user_case: GetLogoutUserCase,
    response: Response,
):  # type: ignore[reportInvalidTypeForm]
    if not token:
        raise UnauthorizedError("No autorizado para realizar esta acción")

    await logout_user_case.execute(token.credentials)

    # Clear auth cookies
    clear_auth_cookies(response)

    return SimpleMessageSchema(message="Sesión cerrada exitosamente")


@auth_router.get(
    path="/users/me",
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    response_model=UserSchema,
)
async def get_current_user_profile(
    current_user: GetCurrentUser,
    get_user_profile_case: GetUserProfileCaseDep,
) -> UserSchema:
    """Return the authenticated user's profile."""
    user = await get_user_profile_case.execute(current_user)
    return UserSchema(
        id=user.id,
        created_at=user.created_at,
        name=user.name,
        dni=user.dni,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        tenant_id=user.tenant_id,
    )


@auth_router.put(
    path="/users/me",
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    response_model=UserSchema,
)
async def update_current_user_profile(
    data: UpdateProfileSchema,
    current_user: GetCurrentUser,
    update_user_profile_case: GetUpdateUserProfileCaseDep,
) -> UserSchema:
    """Update the authenticated user's name and/or email."""
    user = await update_user_profile_case.execute(
        current_user=current_user,
        name=data.name,
        email=data.email,
    )
    return UserSchema(
        id=user.id,
        created_at=user.created_at,
        name=user.name,
        dni=user.dni,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        tenant_id=user.tenant_id,
    )
