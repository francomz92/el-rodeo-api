from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.common.infrastructure.adapters.http.output.errors import StandardErrorResponse
from src.common.infrastructure.core import settings
from src.common.infrastructure.core.app import configure_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    version="0.1.0",
    lifespan=lifespan,
    **settings.EXTRA_APP_CONFIG,
    responses={
        422: {"model": StandardErrorResponse},
    },
)

configure_app(app)
