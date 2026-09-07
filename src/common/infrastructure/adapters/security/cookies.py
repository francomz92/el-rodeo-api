"""Auth cookie utilities for setting and clearing HttpOnly Secure SameSite cookies.

Provides functions to manage access and refresh token cookies for web clients.
"""

from typing import Any

from fastapi import Response


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    settings: Any,  # Settings object — avoids circular imports
) -> None:
    """Set HttpOnly Secure SameSite cookies for access and refresh tokens.

    Args:
        response: FastAPI Response to attach cookies to.
        access_token: JWT access token string.
        refresh_token: JWT refresh token string.
        settings: Application settings (must have COOKIE_DOMAIN, COOKIE_SECURE).
    """
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",  # strict or lax depending on your needs
        path="/",
        max_age=900,  # 15 minutes in seconds
        domain=settings.COOKIE_DOMAIN,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",  # strict or lax depending on your needs
        path="/",
        max_age=604800,  # 7 days in seconds
        domain=settings.COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response, settings: Any) -> None:
    """Clear both auth cookies by setting empty values with max_age=0.

    Args:
        response: FastAPI Response to clear cookies on.
        settings: Application settings (must have COOKIE_DOMAIN, COOKIE_SECURE).
    """
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/api",
        max_age=0,
        domain=settings.COOKIE_DOMAIN,
    )
    response.set_cookie(
        key="refresh_token",
        value="",
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="strict",
        path="/auth/refresh",
        max_age=0,
        domain=settings.COOKIE_DOMAIN,
    )
