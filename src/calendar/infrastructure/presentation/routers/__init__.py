from fastapi import APIRouter

from ._calendar_events import events_router as _events_router

calendar_routers = APIRouter()
calendar_routers.include_router(_events_router, tags=["Calendar / Events"])


__all__ = ["calendar_routers"]
