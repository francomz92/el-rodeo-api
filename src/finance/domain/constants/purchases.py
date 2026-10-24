from enum import StrEnum


class PurchaseStatus(StrEnum):
    """Lifecycle of a purchase: stock moves only after confirmation."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
