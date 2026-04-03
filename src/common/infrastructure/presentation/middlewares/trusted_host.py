from fastapi import FastAPI
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from src.common.infrastructure.core import settings


def configure_trusted_host(app: FastAPI):
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)
