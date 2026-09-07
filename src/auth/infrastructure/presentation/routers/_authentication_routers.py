from fastapi import APIRouter, Request, Response, status

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    ChangePasswordSchema,
    CreateTenantSchema,
    LoginSchema,
)
from src.auth.infrastructure.adapters.http.input.role_schemas import InviteSchema
from src.auth.infrastructure.adapters.http.input.user_schemas import (
    UpdateProfileSchema,
)
from src.auth.infrastructure.adapters.http.output.authentication_schemas import (
    LoginResponseSchema,
    WsTokenResponse,
)
from src.auth.infrastructure.adapters.http.output.tenant_schemas import TenantResponseSchema
from src.auth.infrastructure.adapters.http.output.user_schemas import UserSchema
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetChangePasswordCase,
    GetCreateTenantCase,
    GetCurrentUser,
    GetLoginUserCase,
    GetLogoutUserCase,
    GetOauthToken,
    GetRefreshToken,
    require_role,
)
from src.auth.infrastructure.presentation.dependencies.role_dependencies import (
    GetInviteUserCase,
)
from src.auth.infrastructure.presentation.dependencies.tenant_dependencies import GetObtainTenantCase
from src.auth.infrastructure.presentation.dependencies.user_dependencies import (
    GetUpdateUserProfileCaseDep,
    GetUserProfileCaseDep,
)
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema
from src.common.infrastructure.adapters.security.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

auth_router = APIRouter()


@auth_router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant with OWNER user",
    description="SUPER_ADMIN only. Creates a tenant with the given slug and creates the first user as OWNER.",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.SUPER_ADMIN)],
)
@rate_limit("3/minute")
async def register_user(
    request: Request,
    data: CreateTenantSchema,
    create_tenant_case: GetCreateTenantCase,
):
    return await create_tenant_case.execute(
        tenant_name=data.tenant_name,
        slug=data.slug,
        name=data.name,
        dni=data.dni,
        email=data.email,
        redirect_url=f"{settings.DOMAIN}/confirm-account",
    )


@auth_router.post(
    path="/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite a user to the tenant",
    description="ADMIN or higher. Creates a user with role ≤ inviter's rank in the inviter's tenant.",
    response_model=UserSchema,
    dependencies=[require_role(UserRole.ADMIN)],
)
@rate_limit("5/minute")
async def invite_user(
    request: Request,
    data: InviteSchema,
    current_user: GetCurrentUser,
    invite_user_case: GetInviteUserCase,
):
    return await invite_user_case.execute(
        inviter=current_user,
        name=data.name,
        dni=data.dni,
        email=data.email,
        role=data.role,
        redirect_url=f"{settings.DOMAIN}/confirm-account",
    )


@auth_router.post(
    path="/login",
    status_code=status.HTTP_200_OK,
    summary="Authenticate a registered user",
    description="Returns access and refresh tokens. Sets HttpOnly cookies when X-Requested-With: XMLHttpRequest is present (web clients).",
    response_model=LoginResponseSchema | SimpleMessageSchema,
)
@rate_limit("5/minute")
async def login_user(
    data: LoginSchema,
    login_user_case: GetLoginUserCase,
    request: Request,
    response: Response,
):
    """
    Authenticate a registered user in the system.

    Returns:
        LoginResponseSchema: The access and refresh tokens only for mobile clients.
        - For example:
        ```
        {"access_token": "string", "refresh_token": "string"}
        ```
        MessageSchema: A simple message indicating success to web clients.
        - For example:
        ```
        {"message": "string"}
        ```
    """
    access_token, refresh_token = await login_user_case.execute(
        dni=data.dni,
        password=data.password,
    )

    # Set HttpOnly cookies for web clients (X-Requested-With: XMLHttpRequest)
    requested_with = request.headers.get("x-requested-with", "")
    if requested_with == "XMLHttpRequest":
        set_auth_cookies(response, access_token, refresh_token, settings)
        return SimpleMessageSchema(message="Login successful")

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@auth_router.get(
    path="/ws-token",
    status_code=status.HTTP_200_OK,
    summary="Get a short-lived WebSocket token",
    description="Returns a 5-minute JWT restricted to WebSocket connections. Requires authentication via Bearer token. The client should call this endpoint JUST before opening a WebSocket, passing the access_token in the Authorization header.",
    response_model=WsTokenResponse,
)
@rate_limit("10/minute")
async def get_ws_token(
    current_user: GetCurrentUser,
    token_service: GetTokenService,
    request: Request,
) -> WsTokenResponse:
    """Generate a short-lived WS token (5 min) for real-time notifications.

    The returned token has ``type=ws`` and ``purpose=websocket`` claims and
    is only accepted by the ``/ws/notifications`` WebSocket endpoint.
    """
    ws_token = token_service.generate_ws_token(
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
    )
    return WsTokenResponse(ws_token=ws_token)


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
    refresh_token: GetRefreshToken,
    logout_user_case: GetLogoutUserCase,
    response: Response,
    request: Request,
):  # type: ignore[reportInvalidTypeForm]
    await logout_user_case.execute(token.credentials, refresh_token=refresh_token)
    # Clear auth cookies
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        clear_auth_cookies(response, settings)
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


@auth_router.get(
    path="/users/me/tenant",
    status_code=status.HTTP_200_OK,
    summary="Get current tenant info",
    response_model=TenantResponseSchema,
)
async def get_my_tenant(
    current_user: GetCurrentUser,
    get_tenant_case: GetObtainTenantCase,
):
    """Return the authenticated user's tenant info."""
    return await get_tenant_case.execute(current_user.tenant_id)
