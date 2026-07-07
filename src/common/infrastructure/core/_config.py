import logging
from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.domain.types import EnvironmentType


class Settings(BaseSettings):
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT  # development, staging, production
    TERM_OF_SERVICE_URL: str = "https://el-rodeo-api.com/terms-of-service"
    CORS_ORIGINS: list[str] = ["*"]
    ALLOWED_ORIGINS: list[str] = ["*"]  # backward compat — superseded by CORS_ORIGINS
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
    REDIS_URL: str = "redis://localhost:6380/0"

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

    # ── Audit / Data Retention ─────────────────────────────────────────────────
    AUDIT_RETENTION_DAYS: int = 180

    # ── Billing / Subscription ────────────────────────────────────────────────
    TRIAL_DAYS: int = 14
    MP_ACCESS_TOKEN: str = ""
    MP_WEBHOOK_SECRET: str = ""
    MP_WEBHOOK_URL: str = ""

    # ── Observability ─────────────────────────────────────────────────────────
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: Literal["text", "json"] = "text"
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

    @model_validator(mode="after")
    def _check_wildcard_in_production(self) -> "Settings":
        if self.ENVIRONMENT != EnvironmentType.DEVELOPMENT:
            if "*" in self.CORS_ORIGINS:
                logging.getLogger(__name__).critical(
                    "CORS_ORIGINS contains '*' in non-development environment — this is insecure. Set explicit origins in production."
                )
            if "*" in self.TRUSTED_HOSTS:
                logging.getLogger(__name__).critical(
                    "TRUSTED_HOSTS contains '*' in non-development environment — this is insecure. "
                    "Set explicit allowed hosts in production."
                )
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
