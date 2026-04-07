from fastapi import FastAPI

from src.auth.infrastructure.presentation.routers import auth_router


def configure_routers(app: FastAPI):
    app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
