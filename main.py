from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.common.infrastructure.core import configure_app, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    version="0.1.0",
    lifespan=lifespan,
    **settings.EXTRA_APP_CONFIG,
)

configure_app(app)
