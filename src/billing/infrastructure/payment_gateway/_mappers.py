"""MercadoPago API response mappers.

Extracted from _client.py to reduce file size. Pure functions that
transform MercadoPago API responses into domain types.
"""

from src.billing.application.mappers.subscription_status import map_mp_subscription_status
from src.billing.domain.entities._payment_status import PaymentStatus
from src.billing.domain.exceptions import PaymentGatewayError

__all__ = ["map_mp_status", "map_mp_subscription_status"]


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
