"""Authentication router — login, logout, token refresh, and password change."""

from fastapi import APIRouter, Request, Response, status

from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    ChangePasswordSchema,
    LoginSchema,
)
from src.auth.infrastructure.adapters.http.output.authentication_schemas import (
    LoginResponseSchema,
    RefreshResponseSchema,
    WsTokenResponse,
)
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetChangePasswordCase,
    GetCurrentUser,
    GetLoginUserCase,
    GetLogoutUserCase,
    GetOauthToken,
    GetRefreshToken,
    GetRefreshTokenCase,
)
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema
from src.common.infrastructure.adapters.security.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
)
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.dependencies.token import GetTokenService
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

authentication_router = APIRouter(tags=["Authentication"])


@authentication_router.post(
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
        return SimpleMessageSchema(message="Sesión iniciada exitosamente")

    return LoginResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@authentication_router.get(
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


@authentication_router.post(
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


@authentication_router.post(
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


@authentication_router.post(
    path="/refresh",
    status_code=status.HTTP_200_OK,
    summary="Refresh authentication tokens",
    description="Accepts a valid refresh token and returns a new access+refresh token pair. "
    "The old refresh token is invalidated (rotated). "
    "Rate limited at 10/min per IP.",
    response_model=RefreshResponseSchema | SimpleMessageSchema,
)
@rate_limit("10/minute")
async def refresh_token(
    refresh_token: GetRefreshToken,
    refresh_token_case: GetRefreshTokenCase,
    request: Request,
    response: Response,
):
    """Refresh the access and refresh tokens.

    The old refresh token is invalidated during rotation.
    On success, the new tokens are returned in the response body.
    """
    access_token, new_refresh_token = await refresh_token_case.execute(
        refresh_token=refresh_token,
    )
    if request.headers.get("x-requested-with"):
        set_auth_cookies(response, access_token, new_refresh_token, settings)
        return SimpleMessageSchema(message="Token actualizado exitosamente")

    # Return both tokens in the response body
    return RefreshResponseSchema(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )
