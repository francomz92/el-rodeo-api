from fastapi import FastAPI

from src.auth.infrastructure.presentation.routers import auth_routers
from src.cattle.infrastructure.presentation.routers import cattle_routers
from src.finance.infrastructure.presentation.routers import finance_routers
from src.market.infrastructure.presentation.routers import market_routers


def configure_routers(app: FastAPI):
    app.include_router(auth_routers, prefix="/auth")
    app.include_router(cattle_routers, prefix="/cattle")
    app.include_router(finance_routers, prefix="/finance")
    app.include_router(market_routers, prefix="/market")
