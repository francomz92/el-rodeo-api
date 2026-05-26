from fastapi import APIRouter

from ._animal_protocols import protocols_router as _protocols_router
from ._animal_types import animal_type_router as _animal_type_router
from ._animals import animals_router as _animals_router
from ._schedule_events import events_router as _events_router

cattle_routers = APIRouter()
cattle_routers.include_router(_animals_router, tags=["Cattle / Animals"])
cattle_routers.include_router(_events_router, tags=["Cattle / Events"])
cattle_routers.include_router(_protocols_router, tags=["Cattle / Protocols"])
cattle_routers.include_router(_animal_type_router, tags=["Cattle / AnimalTypes"])


__all__ = ["cattle_routers"]
