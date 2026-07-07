"""Unit tests for auth cookie service.

Verifies that HttpOnly Secure SameSite cookies are set and cleared
correctly for access and refresh tokens.
"""

from unittest.mock import MagicMock

from src.common.infrastructure.adapters.security.cookies import (
    clear_auth_cookies,
    set_auth_cookies,
)


class TestSetAuthCookies:
    """set_auth_cookies sets HttpOnly Secure SameSite cookies."""

    def setup_method(self) -> None:
        self.response = MagicMock()
        self.settings = MagicMock()
        self.settings.COOKIE_DOMAIN = ""
        self.settings.COOKIE_SECURE = True

    def test_sets_access_token_cookie(self) -> None:
        """Access token cookie is set with correct attributes."""
        set_auth_cookies(
            response=self.response,
            access_token="access-123",
            refresh_token="refresh-456",
            settings=self.settings,
        )

        # Verify access token cookie was set
        self.response.set_cookie.assert_any_call(
            key="access_token",
            value="access-123",
            httponly=True,
            secure=True,
            samesite="strict",
            path="/api",
            max_age=900,
            domain="",
        )

    def test_sets_refresh_token_cookie(self) -> None:
        """Refresh token cookie is set with correct attributes."""
        set_auth_cookies(
            response=self.response,
            access_token="access-123",
            refresh_token="refresh-456",
            settings=self.settings,
        )

        # Verify refresh token cookie was set
        self.response.set_cookie.assert_any_call(
            key="refresh_token",
            value="refresh-456",
            httponly=True,
            secure=True,
            samesite="strict",
            path="/auth/refresh",
            max_age=604800,  # 7 days in seconds
            domain="",
        )

    def test_uses_cookie_domain_from_settings(self) -> None:
        """Cookie domain is taken from settings."""
        self.settings.COOKIE_DOMAIN = ".example.com"

        set_auth_cookies(
            response=self.response,
            access_token="access-123",
            refresh_token="refresh-456",
            settings=self.settings,
        )

        call_kwargs = self.response.set_cookie.call_args_list[0].kwargs
        assert call_kwargs["domain"] == ".example.com"

    def test_insecure_when_cookie_secure_false(self) -> None:
        """Cookie secure flag follows settings."""
        self.settings.COOKIE_SECURE = False

        set_auth_cookies(
            response=self.response,
            access_token="access-123",
            refresh_token="refresh-456",
            settings=self.settings,
        )

        call_kwargs = self.response.set_cookie.call_args_list[0].kwargs
        assert call_kwargs["secure"] is False


class TestClearAuthCookies:
    """clear_auth_cookies clears both auth cookies."""

    def setup_method(self) -> None:
        self.response = MagicMock()

    def test_clears_access_token_cookie(self) -> None:
        """Access token cookie is cleared with max_age=0."""
        clear_auth_cookies(self.response)

        self.response.set_cookie.assert_any_call(
            key="access_token",
            value="",
            httponly=True,
            samesite="strict",
            path="/api",
            max_age=0,
        )

    def test_clears_refresh_token_cookie(self) -> None:
        """Refresh token cookie is cleared with max_age=0."""
        clear_auth_cookies(self.response)

        self.response.set_cookie.assert_any_call(
            key="refresh_token",
            value="",
            httponly=True,
            samesite="strict",
            path="/auth/refresh",
            max_age=0,
        )

    def test_clears_both_cookies(self) -> None:
        """Both cookies are cleared in a single call."""
        clear_auth_cookies(self.response)

        assert self.response.set_cookie.call_count >= 2
