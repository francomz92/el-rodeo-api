from enum import StrEnum


class SubscriptionStatus(StrEnum):
    PENDING = "pending"
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELED = "canceled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"
    PAUSED = "paused"
