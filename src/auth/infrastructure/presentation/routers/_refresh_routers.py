from fastapi import APIRouter, Request, Response, status

from src.auth.infrastructure.adapters.http.output.authentication_schemas import (
    RefreshResponseSchema,
)
from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
    GetRefreshToken,
    GetRefreshTokenCase,
)
from src.common.infrastructure.adapters.http.output.messages import SimpleMessageSchema
from src.common.infrastructure.adapters.security.cookies import set_auth_cookies
from src.common.infrastructure.core import settings
from src.common.infrastructure.presentation.middlewares.rate_limiter import rate_limit

refresh_router = APIRouter()


@refresh_router.post(
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
        return SimpleMessageSchema(message="Token refreshed successfully")

    # Return both tokens in the response body
    return RefreshResponseSchema(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )
