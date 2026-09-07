import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.domain.types import EnvironmentType

# Known weak SECRET values that should never be used outside of development.
_WEAK_SECRETS: set[str] = {
    "change-me-to-a-secure-random-secret",
    "change-me",
    "secret",
    "password",
    "default",
    "my-secret",
    "my_secret",
    "mysecret",
    "change_me",
    "changeme",
}


class Settings(BaseSettings):
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT  # development, staging, production
    TERM_OF_SERVICE_URL: str = "https://el-rodeo-api.com/terms-of-service"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]  # backward compat — superseded by CORS_ORIGINS
    ALLOWED_HEADERS: list[str] = ["*"]
    TRUSTED_HOSTS: list[str] = ["*"]
    DB_URL: str
    SECRET: str
    JWT_ALGORITHM: str
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    DOMAIN: str
    BROKER_URL: str
    RESULT_BACKEND_URL: str
    REDIS_URL: str

    # ── Database Connection Pool ──────────────────────────────────────────────
    DB_POOL_SIZE: int = 10
    DB_POOL_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600  # seconds

    # ── Security / Rate Limiting ──────────────────────────────────────────────
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"
    RATE_LIMIT_PASSWORD_CHANGE: str = "3/minute"
    RATE_LIMIT_REFRESH: str = "10/minute"
    ENABLE_RATE_LIMIT: bool = True
    MAX_REQUEST_BODY_SIZE: int = 10_485_760  # 10MB
    CSP_DIRECTIVES_ENABLED: bool = True
    CSP_DEFAULT_SRC: str = "'self'"
    CSP_DIRECTIVES: dict[str, str] = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self' data:",
        "connect-src": "'self'",
        "base-uri": "'self'",
        "form-action": "'self'",
    }
    HSTS_MAX_AGE: int = 31536000
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    WS_TOKEN_EXPIRE_MINUTES: int = 5

    # ── Audit / Data Retention ─────────────────────────────────────────────────
    AUDIT_RETENTION_DAYS: int = 180

    # ── Billing / Subscription ────────────────────────────────────────────────
    TRIAL_DAYS: int = 14
    MP_ACCESS_TOKEN: str = ""
    MP_WEBHOOK_SECRET: str = ""
    MP_WEBHOOK_URL: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Observability ─────────────────────────────────────────────────────────
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: Literal["text", "json"] = "text"
    LOG_DIR: Path = Path("logs")
    PROMETHEUS_ENABLED: bool = False
    OBSERVABILITY_MIDDLEWARE_ENABLED: bool = True

    # ── Security Hardening ────────────────────────────────────────────────────
    DEBUG: bool = True
    SANITIZE_QUERY_KEYS: list[str] = [
        "password",
        "token",
        "secret",
        "key",
        "api_key",
        "access_token",
        "refresh_token",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @field_validator("SECRET", mode="after")
    @classmethod
    def _validate_secret(cls, v: str, info) -> str:
        """Validate SECRET minimum length and reject known weak values."""
        if info.data.get("ENVIRONMENT") != EnvironmentType.DEVELOPMENT:
            if len(v) < 32:
                raise ValueError(f"SECRET must be at least 32 characters (got {len(v)})")
            if v.lower() in _WEAK_SECRETS:
                raise ValueError("SECRET contains a known weak value — use a strong random key instead")
        return v

    @model_validator(mode="after")
    def _check_debug_not_in_production(self) -> "Settings":
        """Prevent DEBUG=True in non-development environments."""
        if self.ENVIRONMENT != EnvironmentType.DEVELOPMENT and self.DEBUG:
            raise ValueError("DEBUG must not be True when ENVIRONMENT is not 'development'")
        return self

    @model_validator(mode="after")
    def _check_wildcard_in_production(self) -> "Settings":
        if self.ENVIRONMENT != EnvironmentType.DEVELOPMENT:
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "CORS_ORIGINS contains '*' in non-development environment — this is insecure. Set explicit origins in production."
                )
            if "*" in self.TRUSTED_HOSTS:
                raise ValueError(
                    "TRUSTED_HOSTS contains '*' in non-development environment — this is insecure. "
                    "Set explicit allowed hosts in production."
                )
        return self

    @model_validator(mode="after")
    def _check_csp_directives(self) -> "Settings":
        if self.ENVIRONMENT != EnvironmentType.DEVELOPMENT:
            if not self.CSP_DIRECTIVES_ENABLED:
                logging.getLogger(__name__).warning("CSP is disabled in %s", self.ENVIRONMENT)
            elif not self.CSP_DIRECTIVES:
                raise ValueError("CSP_DIRECTIVES_ENABLED is True but CSP_DIRECTIVES is not set")
        return self

    @property
    def EXTRA_APP_CONFIG(self) -> dict:
        return {
            "debug": self.DEBUG,
            "title": "El Rodeo API",
            "summary": "API para la gestión de El Rodeo, un gestor de ganado y finanzas para pequeños productores",
            "redirect_slashes": True,
            "terms_of_service": self.TERM_OF_SERVICE_URL,
            "openapi_url": "/openapi.json" if self.DEBUG else None,
            "docs_url": "/docs" if self.DEBUG else None,
        }


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # type: ignore


settings = _get_settings()
