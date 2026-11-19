from fastapi import APIRouter

from src.market.infrastructure.presentation.routers._buyers import buyer_router as _buyer_router
from src.market.infrastructure.presentation.routers._sales import sale_router as _sale_router

market_routers = APIRouter()

market_routers.include_router(_buyer_router, tags=["Market / Buyers"])
market_routers.include_router(_sale_router, tags=["Market / Sales"])

__all__ = ["market_routers"]
