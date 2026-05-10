from fastapi import FastAPI

from src.auth.infrastructure.presentation.routers import auth_routers
from src.cattle.infrastructure.presentation.routers import cattle_routers


def configure_routers(app: FastAPI):
    app.include_router(auth_routers, prefix="/auth", tags=["Authentication"])
    app.include_router(cattle_routers, prefix="/cattle", tags=["Cattle"])
