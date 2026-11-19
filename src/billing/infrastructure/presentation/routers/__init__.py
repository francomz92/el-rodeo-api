"""Billing presentation routers.

Aggregates webhook, subscription, and payment routers into a single
``billing_routers`` that gets registered in ``configure_routers``.
Each router carries its own ``/billing`` path prefix and tags.
"""

from fastapi import APIRouter

from src.billing.infrastructure.presentation.routers._payments import payment_router as _payment_router
from src.billing.infrastructure.presentation.routers._subscriptions import subscription_router as _subscription_router
from src.billing.infrastructure.presentation.routers._webhooks import webhook_router as _webhook_router

billing_routers = APIRouter()
billing_routers.include_router(_webhook_router)
billing_routers.include_router(_subscription_router)
billing_routers.include_router(_payment_router)

__all__ = ["billing_routers"]
