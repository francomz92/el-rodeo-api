from fastapi import APIRouter

from ._animal_supplies import animal_supplies_router as _animal_supplies_router
from ._animal_supply_types import supply_type_router as _supply_type_router
from ._purchases import purchase_router as _purchase_router

finance_routers = APIRouter()


finance_routers.include_router(_animal_supplies_router, tags=["Finance / Supplies"])
finance_routers.include_router(_purchase_router, tags=["Finance / Purchases"])
finance_routers.include_router(_supply_type_router, tags=["Finance / Supply Types"])

__all__ = ["finance_routers"]
