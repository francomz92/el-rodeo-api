"""Unit tests for application configuration settings.

These tests verify that Settings loads correct defaults and
honours environment variable overrides for security-related config.
"""

import logging
from unittest.mock import patch

import pytest

from src.common.infrastructure.core._config import Settings

# Minimal env vars required for Settings to instantiate (required fields).
_REQUIRED_ENV = {
    "DB_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "SECRET": "test-secret-key-for-testing",
    "JWT_ALGORITHM": "HS256",
    "SMTP_SERVER": "smtp.test.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "test@test.com",
    "SMTP_PASSWORD": "testpass",
    "DOMAIN": "http://test.com",
    "BROKER_URL": "redis://localhost:6380/0",
    "RESULT_BACKEND_URL": "redis://localhost:6380/0",
}


def _make_settings(**overrides: str) -> Settings:
    """Create a Settings instance with required env vars plus optional overrides.

    Uses clean env to prevent .env file interference.
    """
    env = {**_REQUIRED_ENV, **overrides}
    with patch.dict("os.environ", env, clear=True):
        return Settings(_env_file=None)


class TestSecuritySettings:
    """Security-related configuration settings."""

    def test_default_cookie_domain_is_empty(self) -> None:
        """COOKIE_DOMAIN defaults to empty string (same domain)."""
        settings = _make_settings()
        assert settings.COOKIE_DOMAIN == ""

    def test_cookie_secure_defaults_to_true(self) -> None:
        """COOKIE_SECURE defaults to True when not overridden."""
        settings = _make_settings()
        assert settings.COOKIE_SECURE is True

    def test_rate_limit_defaults(self) -> None:
        """Rate limit env vars have correct defaults."""
        settings = _make_settings()
        assert settings.RATE_LIMIT_DEFAULT == "100/minute"
        assert settings.RATE_LIMIT_LOGIN == "5/minute"
        assert settings.RATE_LIMIT_REGISTER == "3/minute"
        assert settings.RATE_LIMIT_PASSWORD_CHANGE == "3/minute"
        assert settings.RATE_LIMIT_REFRESH == "10/minute"

    def test_csp_default_src_default(self) -> None:
        """CSP default-src defaults to 'self'."""
        settings = _make_settings()
        assert settings.CSP_DEFAULT_SRC == "'self'"

    def test_hsts_max_age_default(self) -> None:
        """HSTS max-age defaults to 31536000 (1 year in seconds)."""
        settings = _make_settings()
        assert settings.HSTS_MAX_AGE == 31536000

    def test_token_expiry_defaults(self) -> None:
        """Token expiry settings have correct defaults."""
        settings = _make_settings()
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 15
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_env_override_cookie_secure(self) -> None:
        """COOKIE_SECURE can be overridden via env var."""
        settings = _make_settings(COOKIE_SECURE="false")
        assert settings.COOKIE_SECURE is False

    def test_env_override_rate_limit_login(self) -> None:
        """RATE_LIMIT_LOGIN can be overridden via env var."""
        settings = _make_settings(RATE_LIMIT_LOGIN="10/minute")
        assert settings.RATE_LIMIT_LOGIN == "10/minute"

    def test_cors_origins_defaults_to_wildcard(self) -> None:
        """CORS_ORIGINS defaults to ['*']."""
        settings = _make_settings()
        assert settings.CORS_ORIGINS == ["*"]

    def test_cors_origins_can_be_overridden(self) -> None:
        """CORS_ORIGINS accepts custom origins."""
        settings = _make_settings(CORS_ORIGINS='["https://example.com"]')
        assert settings.CORS_ORIGINS == ["https://example.com"]

    def test_debug_defaults_to_true(self) -> None:
        """DEBUG defaults to True."""
        settings = _make_settings()
        assert settings.DEBUG is True

    def test_debug_can_be_false_in_production(self) -> None:
        """DEBUG can be set to False for production."""
        settings = _make_settings(DEBUG="false")
        assert settings.DEBUG is False

    def test_max_request_body_size_defaults_to_10mb(self) -> None:
        """MAX_REQUEST_BODY_SIZE defaults to 10_485_760 (10MB)."""
        settings = _make_settings()
        assert settings.MAX_REQUEST_BODY_SIZE == 10_485_760

    def test_max_request_body_size_can_be_overridden(self) -> None:
        """MAX_REQUEST_BODY_SIZE can be overridden."""
        settings = _make_settings(MAX_REQUEST_BODY_SIZE="5242880")
        assert settings.MAX_REQUEST_BODY_SIZE == 5_242_880

    def test_rate_limit_default_can_be_overridden(self) -> None:
        """RATE_LIMIT_DEFAULT can be overridden via env var."""
        settings = _make_settings(RATE_LIMIT_DEFAULT="200/minute")
        assert settings.RATE_LIMIT_DEFAULT == "200/minute"

    def test_csp_directives_defaults(self) -> None:
        """CSP_DIRECTIVES defaults to expanded policy dict."""
        settings = _make_settings()
        assert settings.CSP_DIRECTIVES is not None
        assert settings.CSP_DIRECTIVES["default-src"] == "'self'"
        assert settings.CSP_DIRECTIVES["script-src"] == "'self'"
        assert settings.CSP_DIRECTIVES["style-src"] == "'self'"
        assert settings.CSP_DIRECTIVES["img-src"] == "'self' data:"
        assert settings.CSP_DIRECTIVES["connect-src"] == "'self'"
        assert settings.CSP_DIRECTIVES["base-uri"] == "'self'"
        assert settings.CSP_DIRECTIVES["form-action"] == "'self'"

    def test_csp_directives_can_be_configured(self) -> None:
        """CSP_DIRECTIVES can be overridden via env var."""
        custom = '{"default-src": "https://example.com", "script-src": "https://cdn.example.com"}'
        settings = _make_settings(CSP_DIRECTIVES=custom)
        assert settings.CSP_DIRECTIVES["default-src"] == "https://example.com"
        assert settings.CSP_DIRECTIVES["script-src"] == "https://cdn.example.com"

    def test_csp_directives_includes_all_directives(self) -> None:
        """CSP_DIRECTIVES contains all required directives."""
        settings = _make_settings()
        expected = {
            "default-src",
            "script-src",
            "style-src",
            "img-src",
            "connect-src",
            "base-uri",
            "form-action",
        }
        assert expected.issubset(settings.CSP_DIRECTIVES.keys())


class TestConfigValidation:
    """Validation logic in Settings."""

    def test_wildcard_cors_logs_critical_in_production(self, caplog: pytest.LogCaptureFixture) -> None:
        """CRITICAL is logged in production when CORS_ORIGINS contains '*'."""
        caplog.set_level(logging.CRITICAL)
        _make_settings(ENVIRONMENT="production", CORS_ORIGINS='["*"]')
        assert any("CORS_ORIGINS contains '*'" in record.getMessage() for record in caplog.records)

    def test_wildcard_trusted_hosts_logs_critical_in_production(self, caplog: pytest.LogCaptureFixture) -> None:
        """CRITICAL is logged in production when TRUSTED_HOSTS contains '*'."""
        caplog.set_level(logging.CRITICAL)
        _make_settings(ENVIRONMENT="production", TRUSTED_HOSTS='["*"]')
        assert any("TRUSTED_HOSTS contains '*'" in record.getMessage() for record in caplog.records)

    def test_no_critical_logged_in_dev_with_wildcard(self, caplog: pytest.LogCaptureFixture) -> None:
        """No CRITICAL warning is logged in development mode with wildcard."""
        caplog.set_level(logging.CRITICAL)
        _make_settings(ENVIRONMENT="development", CORS_ORIGINS='["*"]', TRUSTED_HOSTS='["*"]')
        critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
        assert len(critical_records) == 0


class TestPoolSettings:
    """Database connection pool configuration settings."""

    def test_default_pool_size(self) -> None:
        """DB_POOL_SIZE defaults to 10."""
        settings = _make_settings()
        assert settings.DB_POOL_SIZE == 10

    def test_default_pool_overflow(self) -> None:
        """DB_POOL_OVERFLOW defaults to 20."""
        settings = _make_settings()
        assert settings.DB_POOL_OVERFLOW == 20

    def test_default_pool_recycle(self) -> None:
        """DB_POOL_RECYCLE defaults to 3600 (1 hour in seconds)."""
        settings = _make_settings()
        assert settings.DB_POOL_RECYCLE == 3600

    def test_pool_size_can_be_overridden(self) -> None:
        """DB_POOL_SIZE can be overridden via env var."""
        settings = _make_settings(DB_POOL_SIZE="20")
        assert settings.DB_POOL_SIZE == 20

    def test_pool_overflow_can_be_overridden(self) -> None:
        """DB_POOL_OVERFLOW can be overridden via env var."""
        settings = _make_settings(DB_POOL_OVERFLOW="40")
        assert settings.DB_POOL_OVERFLOW == 40

    def test_pool_recycle_can_be_overridden(self) -> None:
        """DB_POOL_RECYCLE can be overridden via env var."""
        settings = _make_settings(DB_POOL_RECYCLE="1800")
        assert settings.DB_POOL_RECYCLE == 1800
