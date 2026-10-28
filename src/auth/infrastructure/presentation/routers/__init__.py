from fastapi import APIRouter

from ._authentication import authentication_router as _authentication_router
from ._tenants import tenant_router as _tenant_router
from ._users import user_router as _user_router

auth_routers = APIRouter()
auth_routers.include_router(_tenant_router)
auth_routers.include_router(_authentication_router)
auth_routers.include_router(_user_router)


__all__ = ["auth_routers"]
