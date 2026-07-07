from fastapi import APIRouter

from ._authentication_routers import auth_router as _auth_router
from ._gdpr_routers import gdpr_router as _gdpr_router
from ._refresh_routers import refresh_router as _refresh_router
from ._role_routers import role_router as _role_router

auth_routers = APIRouter()
auth_routers.include_router(_auth_router, tags=["Authentication"])
auth_routers.include_router(_refresh_router, tags=["Authentication"])
auth_routers.include_router(_role_router, prefix="/users", tags=["Role Management"])
auth_routers.include_router(_gdpr_router, prefix="/users", tags=["GDPR"])


__all__ = ["auth_routers"]
