from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.common.infrastructure.core import settings


def configure_cors(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=settings.ALLOWED_HEADERS,
        allow_credentials=True,
    )
