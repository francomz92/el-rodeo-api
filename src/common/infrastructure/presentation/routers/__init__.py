from fastapi import FastAPI

from src.auth.infrastructure.presentation.routers import auth_routers
from src.billing.infrastructure.presentation.routers import billing_routers
from src.calendar.infrastructure.presentation.routers import calendar_routers
from src.cattle.infrastructure.presentation.routers import cattle_routers
from src.finance.infrastructure.presentation.routers import finance_routers
from src.market.infrastructure.presentation.routers import market_routers
from src.reports.infrastructure.presentation.routers.reports import router as reports_router

from .health import health_router
from .webhook_subscriptions import router as webhook_subscriptions_router
from .ws import router as ws_router


def configure_routers(app: FastAPI):
    app.include_router(health_router)
    app.include_router(auth_routers, prefix="/auth")
    app.include_router(billing_routers)
    app.include_router(cattle_routers, prefix="/cattle")
    app.include_router(calendar_routers, prefix="/calendar")
    app.include_router(finance_routers, prefix="/finance")
    app.include_router(market_routers, prefix="/market")
    app.include_router(webhook_subscriptions_router)
    app.include_router(reports_router)
    app.include_router(ws_router)
