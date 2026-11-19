from fastapi import APIRouter

from src.auth.infrastructure.presentation.routers._authentication import authentication_router as _authentication_router
from src.auth.infrastructure.presentation.routers._tenants import tenant_router as _tenant_router
from src.auth.infrastructure.presentation.routers._users import user_router as _user_router

auth_routers = APIRouter()
auth_routers.include_router(_tenant_router)
auth_routers.include_router(_authentication_router)
auth_routers.include_router(_user_router)


__all__ = ["auth_routers"]
