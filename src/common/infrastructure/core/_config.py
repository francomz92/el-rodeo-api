from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.common.domain.types import EnvironmentType


class Settings(BaseSettings):
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT  # development, staging, production
    TERM_OF_SERVICE_URL: str = "https://el-rodeo-api.com/terms-of-service"
    ALLOWED_ORIGINS: list[str] = ["*"]
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def EXTRA_APP_CONFIG(self) -> dict:
        return {
            "debug": self.DEBUG,
            "title": "El Rodeo API",
            "summary": "API para la gestión de El Rodeo, un gestor de ganado y finanzas para pequeños productores",
            "redirect_slashes": True,
            "terms_of_service": self.TERM_OF_SERVICE_URL,
            "openapi_url": "/openapi.json" if self.DEBUG else None,
            "docs_url": "/docs",
        }


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # type: ignore


settings = _get_settings()
