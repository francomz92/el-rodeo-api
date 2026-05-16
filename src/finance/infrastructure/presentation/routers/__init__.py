from fastapi import APIRouter

from ._animal_supplies import animal_supplies_router as _animal_supplies_router

finance_routers = APIRouter()


finance_routers.include_router(_animal_supplies_router, prefix="/animal-supplies", tags=["animal-supplies"])

__all__ = ["finance_routers"]
