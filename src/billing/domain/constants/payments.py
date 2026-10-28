from enum import StrEnum


class PaymentStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REFUNDED = "refunded"
    CANCELED = "canceled"
    CHARGED_BACK = "charged_back"
