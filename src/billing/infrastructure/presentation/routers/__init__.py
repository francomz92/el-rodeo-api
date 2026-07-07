"""Billing presentation routers.

Aggregates webhook, subscription, and payment routers into a single
``billing_routers`` that gets registered in ``configure_routers``.
"""

from fastapi import APIRouter

from ._payment_router import payment_router as _payment_router
from ._subscription_router import subscription_router as _subscription_router
from ._webhook_router import webhook_router as _webhook_router

billing_routers = APIRouter()
billing_routers.include_router(_webhook_router)  # Already has /billing prefix
billing_routers.include_router(_subscription_router, prefix="/billing")
billing_routers.include_router(_payment_router, prefix="/billing")

__all__ = ["billing_routers"]
