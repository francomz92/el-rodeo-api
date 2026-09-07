"""MercadoPago API response mappers.

Extracted from _client.py to reduce file size. Pure functions that
transform MercadoPago API responses into domain types.
"""

from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.entities._subscription_status import SubscriptionStatus
from src.billing.domain.exceptions import PaymentGatewayError


def map_mp_status(mp_status: str) -> PaymentStatus:
    """Map MercadoPago payment status to PaymentStatus enum."""
    mapping = {
        "pending": PaymentStatus.PENDING,
        "approved": PaymentStatus.APPROVED,
        "rejected": PaymentStatus.REJECTED,
        "refunded": PaymentStatus.REFUNDED,
        "cancelled": PaymentStatus.CANCELED,
        "in_process": PaymentStatus.PENDING,
        "in_mediation": PaymentStatus.PENDING,
        "charged_back": PaymentStatus.CHARGED_BACK,
    }
    if mp_status not in mapping:
        raise PaymentGatewayError(f"Unknown MercadoPago payment status: {mp_status}")
    return mapping[mp_status]


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
