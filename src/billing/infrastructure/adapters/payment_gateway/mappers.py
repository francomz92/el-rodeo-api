"""MercadoPago API response mappers.

Extracted from _client.py to reduce file size. Pure functions that
transform MercadoPago API responses into domain types.
"""

from src.billing.domain.constants.payments import PaymentStatus
from src.billing.domain.constants.subscriptions import SubscriptionStatus
from src.billing.domain.exceptions import PaymentGatewayError

__all__ = ["map_mp_status", "map_mp_subscription_status", "map_subscription_status_to_mp"]


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
        raise PaymentGatewayError(f"Estado de pago de MercadoPago desconocido: {mp_status}")
    return mapping[mp_status]


def map_mp_subscription_status(mp_status: str) -> SubscriptionStatus | None:
    """Map MercadoPago subscription status to SubscriptionStatus enum.

    ``"pending"`` carries NO authority over the local status: the
    preapproval exists but its first charge has not been collected, and
    the local subscription may legitimately be ACTIVE (charging) or
    TRIAL (fresh signup). Returning ``None`` keeps the local status
    (Fase 4 #4 — mapping ``pending`` to TRIAL let a pending preapproval
    notification downgrade an ACTIVE subscription).
    """
    mapping: dict[str, SubscriptionStatus | None] = {
        "authorized": SubscriptionStatus.ACTIVE,
        "cancelled": SubscriptionStatus.CANCELED,
        "paused": SubscriptionStatus.PAUSED,
        # MP "pending" = awaiting first charge => keep the local status.
        "pending": None,
    }
    if mp_status not in mapping:
        raise PaymentGatewayError(f"Estado de suscripción de MercadoPago desconocido: {mp_status}")
    return mapping[mp_status]


def map_subscription_status_to_mp(status: SubscriptionStatus) -> str:
    """Map a domain SubscriptionStatus to the MercadoPago preapproval spelling.

    Reverse direction of :func:`map_mp_subscription_status` and the single
    conversion point between the two vocabularies: the gateway spells the
    cancel state ``"cancelled"`` (double l) while the domain enum value is
    ``"canceled"``. Only states that are actually sent to the gateway are
    mapped; anything else has no MercadoPago spelling and raises.
    """
    mapping = {
        SubscriptionStatus.ACTIVE: "authorized",
        SubscriptionStatus.CANCELED: "cancelled",
        SubscriptionStatus.PAUSED: "paused",
        SubscriptionStatus.TRIAL: "pending",
    }
    if status not in mapping:
        raise PaymentGatewayError(f"El estado de suscripción {status.value} no tiene equivalente en MercadoPago")
    return mapping[status]
