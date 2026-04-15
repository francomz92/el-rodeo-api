from fastapi import FastAPI

from src.auth.infrastructure.presentation.routers import auth_router
from src.cattle.infrastructure.presentation.routers import animals_router


def configure_routers(app: FastAPI):
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    app.include_router(animals_router, prefix="/cattle", tags=["Cattle"])
