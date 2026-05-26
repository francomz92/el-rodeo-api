from fastapi import APIRouter

from ._authentication_routers import auth_router as _auth_router

auth_routers = APIRouter()
auth_routers.include_router(_auth_router)


__all__ = ["auth_routers"]
