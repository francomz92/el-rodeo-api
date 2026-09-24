"""MercadoPago subscription status mapping for application services."""

from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PaymentGatewayError


def map_mp_subscription_status(mp_status: str) -> SubscriptionStatus:
    """Map MercadoPago subscription status to SubscriptionStatus enum."""
    mapping = {
        "authorized": SubscriptionStatus.ACTIVE,
        "cancelled": SubscriptionStatus.CANCELED,
        "paused": SubscriptionStatus.PAUSED,
        "pending": SubscriptionStatus.TRIAL,
    }
    if mp_status not in mapping:
        raise PaymentGatewayError(f"Unknown MercadoPago subscription status: {mp_status}")
    return mapping[mp_status]
