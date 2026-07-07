"""Unit tests for rate limiter configuration.

Verifies that the rate limiter module initialises correctly with
per-endpoint limits from settings and exempts health/static paths.
"""

from unittest.mock import MagicMock

from slowapi import Limiter

from src.common.infrastructure.presentation.middlewares.rate_limiter import (
    configure_rate_limiter,
    get_rate_limit_limits,
)


class TestGetRateLimitLimits:
    """get_rate_limit_limits extracts per-endpoint limits from settings."""

    def test_returns_limits_from_settings(self) -> None:
        """Extracts all rate limit settings as a dict."""
        settings = MagicMock()
        settings.RATE_LIMIT_LOGIN = "5/minute"
        settings.RATE_LIMIT_REGISTER = "3/minute"
        settings.RATE_LIMIT_PASSWORD_CHANGE = "3/minute"
        settings.RATE_LIMIT_REFRESH = "10/minute"

        limits = get_rate_limit_limits(settings)
        assert limits["login"] == "5/minute"
        assert limits["register"] == "3/minute"
        assert limits["password_change"] == "3/minute"
        assert limits["refresh"] == "10/minute"

    def test_has_exempt_paths(self) -> None:
        """Health and static paths are included as exempt."""
        from src.common.infrastructure.presentation.middlewares.rate_limiter import (
            EXEMPT_PATHS,
        )

        assert "/health" in EXEMPT_PATHS


class TestConfigureRateLimiter:
    """configure_rate_limiter initialises the Limiter and attaches to the app."""

    def test_returns_limiter_instance(self) -> None:
        """Returns a configured Limiter instance."""
        app = MagicMock()
        settings = MagicMock()
        settings.REDIS_URL = "redis://localhost:6380/0"
        settings.RATE_LIMIT_LOGIN = "5/minute"
        settings.RATE_LIMIT_REGISTER = "3/minute"
        settings.RATE_LIMIT_PASSWORD_CHANGE = "3/minute"
        settings.RATE_LIMIT_REFRESH = "10/minute"
        # Prevent actual Redis connection during test
        settings.ENVIRONMENT = "development"

        limiter = configure_rate_limiter(app, settings)

        assert isinstance(limiter, Limiter)

    def test_attaches_limiter_to_app(self) -> None:
        """The limiter is stored on the app state."""
        app = MagicMock()
        app.state = MagicMock()
        settings = MagicMock()
        settings.REDIS_URL = "redis://localhost:6380/0"
        settings.RATE_LIMIT_LOGIN = "5/minute"
        settings.RATE_LIMIT_REGISTER = "3/minute"
        settings.RATE_LIMIT_PASSWORD_CHANGE = "3/minute"
        settings.RATE_LIMIT_REFRESH = "10/minute"
        settings.ENVIRONMENT = "development"

        limiter = configure_rate_limiter(app, settings)

        assert app.state.limiter == limiter
