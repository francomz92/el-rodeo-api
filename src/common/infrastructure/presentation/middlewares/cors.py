from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.infrastructure.core import settings
from src.common.utils import log


def configure_cors(app: FastAPI) -> None:
    origins = settings.CORS_ORIGINS
    has_wildcard = "*" in origins

    if has_wildcard:
        log.warning("CORS_ORIGINS contains '*' — CORS credentials have been disabled for security. Set explicit origins in production.")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=settings.ALLOWED_HEADERS,
        allow_credentials=not has_wildcard,
    )
